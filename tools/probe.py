#!/usr/bin/env python3
"""Actively reads registers from ONE device. Read-only (function 3/4).

The Modbus bus allows a single master. Disconnect the device from the CU2
(or use a port the CU2 does not use) before running this, otherwise both
masters talk at once and you get garbage or worse.

  python tools/probe.py --port /dev/ttyUSB0 --addr 1 --start 0x0100 --count 0x23 \\
      --map registers/srne_mc.yaml
  python tools/probe.py --port /dev/ttyUSB0 --scan-addr      # find the slave id
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from srne.modbus import crc_ok, decode, read_request  # noqa: E402
from srne.regmap import RegisterMap  # noqa: E402

MAX_PER_REQUEST = 20  # SRNE firmware rejects larger blocks on some models


def transact(ser, addr: int, start: int, count: int, fc: int) -> list[int] | str:
    ser.reset_input_buffer()
    ser.write(read_request(addr, start, count, fc))
    expected = 5 + 2 * count
    resp = bytearray()
    deadline = time.time() + 0.5
    while time.time() < deadline and len(resp) < expected:
        resp.extend(ser.read(expected - len(resp)))
        if len(resp) >= 5 and resp[1] & 0x80:
            break
    if not resp:
        return "timeout"
    frame = bytes(resp[:5]) if resp[1] & 0x80 else bytes(resp)
    if not crc_ok(frame):
        return f"bad crc: {bytes(resp).hex(' ')}"
    f = decode(frame)
    if f.kind == "exception":
        return f"exception {f.exception}"
    return f.values


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--addr", type=lambda s: int(s, 0), default=1)
    ap.add_argument("--start", type=lambda s: int(s, 0), default=0x0100)
    ap.add_argument("--count", type=lambda s: int(s, 0), default=0x10)
    ap.add_argument("--fc", type=int, choices=(3, 4), default=3)
    ap.add_argument("--map", help="register map YAML")
    ap.add_argument("--scan-addr", action="store_true", help="try slave ids 1..247 and 255")
    args = ap.parse_args()

    import serial

    ser = serial.Serial(args.port, args.baud, timeout=0.1)

    if args.scan_addr:
        for addr in [*range(1, 248), 255]:
            res = transact(ser, addr, args.start, 1, args.fc)
            if res != "timeout":
                print(f"slave {addr}: {res}")
        return

    rmap = RegisterMap.load(args.map) if args.map else RegisterMap.empty()
    pos, end = args.start, args.start + args.count
    while pos < end:
        n = min(MAX_PER_REQUEST, end - pos)
        res = transact(ser, args.addr, pos, n, args.fc)
        if isinstance(res, str):
            print(f"{pos:#06x} x{n}: {res}")
        else:
            for addr, name, value in rmap.decode_block(pos, res):
                print(f"{addr:#06x} {name:<32} {value}")
        pos += n


if __name__ == "__main__":
    main()
