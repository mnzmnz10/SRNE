"""Modbus RTU framing helpers for passive sniffing.

The sniffer sees a raw byte stream containing both master requests and slave
responses. On a USB-RS485 adapter the inter-frame gap timing is not reliable,
so frames are recovered by trying the lengths each function code allows and
keeping the one whose CRC matches.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MAX_FRAME = 256


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def crc_ok(frame: bytes) -> bool:
    if len(frame) < 4:
        return False
    return crc16(frame[:-2]) == int.from_bytes(frame[-2:], "little")


def with_crc(payload: bytes) -> bytes:
    return payload + crc16(payload).to_bytes(2, "little")


def read_request(addr: int, start: int, count: int, fc: int = 3) -> bytes:
    return with_crc(bytes([addr, fc]) + start.to_bytes(2, "big") + count.to_bytes(2, "big"))


@dataclass
class Frame:
    raw: bytes
    ts: float = 0.0
    addr: int = 0
    fc: int = 0
    # "request", "response", "exception" or "unknown"
    kind: str = "unknown"
    start: int | None = None
    count: int | None = None
    values: list[int] = field(default_factory=list)
    exception: int | None = None

    def hex(self) -> str:
        return self.raw.hex(" ")


def candidate_lengths(buf: bytes) -> list[int]:
    """Frame lengths that are possible given the header bytes seen so far."""
    if len(buf) < 2:
        return []
    fc = buf[1]
    if fc & 0x80:
        return [5]
    if fc in (1, 2, 3, 4):
        lens = [8]
        if len(buf) >= 3:
            lens.append(5 + buf[2])
        return lens
    if fc in (5, 6):
        return [8]
    if fc in (15, 16):
        lens = [8]
        if len(buf) >= 7:
            lens.append(9 + buf[6])
        return lens
    # Vendor specific / unknown function code: brute force every length.
    return list(range(4, MAX_FRAME + 1))


def decode(raw: bytes, ts: float = 0.0) -> Frame:
    f = Frame(raw=raw, ts=ts, addr=raw[0], fc=raw[1])
    body = raw[2:-2]
    fc = f.fc
    if fc & 0x80 and len(raw) == 5:
        f.kind, f.exception = "exception", raw[2]
    elif fc in (3, 4):
        # A response is 5 + an even byte count, so its length is always odd;
        # an 8-byte frame can only be a request.
        if len(raw) == 8:
            f.kind = "request"
            f.start = int.from_bytes(body[0:2], "big")
            f.count = int.from_bytes(body[2:4], "big")
            return f
        n = body[0]
        if len(body) == n + 1 and n % 2 == 0:
            f.kind = "response"
            f.values = [int.from_bytes(body[1 + i:3 + i], "big") for i in range(0, n, 2)]
    elif fc == 6 and len(raw) == 8:
        # Request and echo response are identical; the tracker sorts them out.
        f.kind = "write"
        f.start = int.from_bytes(body[0:2], "big")
        f.values = [int.from_bytes(body[2:4], "big")]
        f.count = 1
    elif fc == 16:
        f.start = int.from_bytes(body[0:2], "big")
        f.count = int.from_bytes(body[2:4], "big")
        if len(raw) == 8:
            f.kind = "response"
        else:
            f.kind = "request"
            data = body[5:]
            f.values = [int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2)]
    return f


class StreamSplitter:
    """Recovers CRC-valid frames from an unframed byte stream."""

    def __init__(self) -> None:
        self.buf = bytearray()
        self.garbage = 0

    def feed(self, data: bytes, ts: float = 0.0) -> list[Frame]:
        self.buf.extend(data)
        out: list[Frame] = []
        while len(self.buf) >= 4:
            lens = candidate_lengths(self.buf)
            match = next((n for n in lens if n <= len(self.buf) and crc_ok(bytes(self.buf[:n]))), None)
            if match:
                out.append(decode(bytes(self.buf[:match]), ts))
                del self.buf[:match]
                continue
            # A complete frame with a standard function code further ahead
            # means the bytes before it are noise.
            skip = self._next_known_frame()
            if skip:
                del self.buf[:skip]
                self.garbage += skip
                continue
            # Otherwise wait if a plausible length has not fully arrived yet.
            if len(self.buf) < MAX_FRAME and any(n > len(self.buf) for n in lens):
                break
            del self.buf[0]
            self.garbage += 1
        return out

    def _next_known_frame(self) -> int:
        for k in range(1, len(self.buf) - 3):
            head = self.buf[k:]
            if head[1] & 0x7F not in (1, 2, 3, 4, 5, 6, 15, 16):
                continue
            if any(n <= len(head) and crc_ok(bytes(head[:n])) for n in candidate_lengths(head)):
                return k
        return 0


@dataclass
class Transaction:
    ts: float
    addr: int
    fc: int
    start: int
    values: list[int]
    op: str  # "read" or "write"


class Tracker:
    """Pairs requests with responses so each value gets a register address."""

    def __init__(self) -> None:
        self.pending: dict[int, Frame] = {}

    def push(self, f: Frame) -> Transaction | None:
        if f.kind == "request":
            self.pending[f.addr] = f
            return None
        if f.kind == "write":
            prev = self.pending.get(f.addr)
            if prev and prev.kind == "write" and prev.raw == f.raw:
                # Second copy is the slave echo; the write is confirmed.
                del self.pending[f.addr]
                return Transaction(f.ts, f.addr, f.fc, f.start or 0, f.values, "write")
            self.pending[f.addr] = f
            return None
        req = self.pending.pop(f.addr, None)
        if f.kind == "response" and req is not None and req.fc == f.fc:
            if f.fc in (3, 4) and req.count == len(f.values):
                return Transaction(f.ts, f.addr, f.fc, req.start or 0, f.values, "read")
            if f.fc == 16:
                return Transaction(f.ts, f.addr, f.fc, req.start or 0, req.values, "write")
        return None
