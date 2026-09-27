#!/usr/bin/env python3
"""Passive RS485 sniffer for the SRNE bus (CU2 <-> devices).

Only listens: it never transmits, so it is safe to attach while the CU2 is
polling the devices.

Examples:
  # USB-RS485 adapter tapped onto the bus, raw bytes also saved for replay
  python tools/sniff.py --port /dev/ttyUSB0 --baud 9600 --raw cap.bin --jsonl cap.jsonl

  # ESP32 sniffer firmware (firmware/esp32-sniffer) that already splits frames
  python tools/sniff.py --esp32 /dev/ttyUSB0 --jsonl cap.jsonl

  # Unknown protocol? Just dump bytes grouped by idle gaps
  python tools/sniff.py --port /dev/ttyUSB0 --baud 9600 --hexdump

  # Replay a saved capture with a register map for slave address 1
  python tools/sniff.py --replay cap.bin --map 1=registers/srne_mc.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from srne.modbus import Frame, StreamSplitter, Tracker, crc_ok, decode  # noqa: E402
from srne.regmap import RegisterMap  # noqa: E402


def parse_maps(specs: list[str]) -> dict[int, RegisterMap]:
    maps = {}
    for spec in specs:
        addr, _, path = spec.partition("=")
        maps[int(addr, 0)] = RegisterMap.load(path)
    return maps


def open_serial(port: str, baud: int):
    import serial

    return serial.Serial(port, baud, timeout=0.02)


def dump_line(ts: float, chunk: bytes) -> str:
    # ASCII column makes text protocols (e.g. Pylontech RS485 "~20...") obvious.
    text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    return f"{ts:.3f}  {chunk.hex(' ')}  |{text}|"


def frames_from_serial(ser, raw_out, hexdump: bool, gap: float):
    splitter = StreamSplitter()
    chunk = bytearray()
    last = time.time()
    while True:
        data = ser.read(256)
        now = time.time()
        if data:
            if raw_out:
                raw_out.write(data)
                raw_out.flush()
            if hexdump:
                if chunk and now - last > gap:
                    print(dump_line(last, bytes(chunk)))
                    chunk.clear()
                chunk.extend(data)
                last = now
                continue
            yield from splitter.feed(data, now)
        elif hexdump and chunk and now - last > gap:
            print(dump_line(last, bytes(chunk)))
            chunk.clear()


def frames_from_replay(path: str):
    splitter = StreamSplitter()
    data = Path(path).read_bytes()
    for i in range(0, len(data), 64):
        yield from splitter.feed(data[i:i + 64], 0.0)
    if splitter.garbage:
        print(f"# {splitter.garbage} bytes did not form CRC-valid Modbus frames", file=sys.stderr)


def frames_from_esp32_lines(lines):
    """Lines look like 'F <millis> <hex bytes>' (see firmware/esp32-sniffer)."""
    for line in lines:
        if isinstance(line, bytes):
            line = line.decode("ascii", "replace")
        parts = line.strip().split(maxsplit=2)
        if len(parts) < 3 or parts[0] != "F":
            if line.strip():
                print(f"# {line.strip()}", file=sys.stderr)
            continue
        raw = bytes.fromhex(parts[2])
        ts = int(parts[1]) / 1000
        if crc_ok(raw):
            yield decode(raw, ts)
        else:
            # Keep non-Modbus traffic visible: it may be a proprietary protocol.
            yield Frame(raw=raw, ts=ts, kind="bad-crc")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--port", help="USB-RS485 serial port")
    src.add_argument("--esp32", help="serial port of the ESP32 sniffer firmware")
    src.add_argument("--replay", help="raw capture file written with --raw")
    src.add_argument("--replay-esp32", help="text log of ESP32 sniffer output")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--map", action="append", default=[], metavar="ADDR=FILE",
                    help="register map for a slave address (repeatable)")
    ap.add_argument("--raw", help="also save raw received bytes to this file")
    ap.add_argument("--jsonl", help="append decoded frames/transactions to this file")
    ap.add_argument("--hexdump", action="store_true", help="print raw bytes only, no Modbus decoding")
    ap.add_argument("--gap", type=float, default=0.01, help="idle gap (s) that separates hexdump chunks")
    ap.add_argument("--quiet-frames", action="store_true", help="print only decoded transactions")
    args = ap.parse_args()

    maps = parse_maps(args.map)
    raw_out = open(args.raw, "ab") if args.raw else None
    jsonl = open(args.jsonl, "a", encoding="utf-8") if args.jsonl else None

    if args.port:
        frames = frames_from_serial(open_serial(args.port, args.baud), raw_out, args.hexdump, args.gap)
    elif args.esp32:
        ser = open_serial(args.esp32, 921600)
        ser.timeout = None
        frames = frames_from_esp32_lines(iter(ser.readline, b""))
    elif args.replay:
        frames = frames_from_replay(args.replay)
    else:
        frames = frames_from_esp32_lines(open(args.replay_esp32, encoding="ascii", errors="replace"))

    tracker = Tracker()
    try:
        for f in frames:
            if not args.quiet_frames:
                desc = f"start={f.start:#06x} count={f.count}" if f.start is not None else ""
                print(f"{f.ts:.3f} addr={f.addr:<3} fc={f.fc:<3} {f.kind:<9} {desc:<24} {f.hex()}")
            if jsonl:
                jsonl.write(json.dumps({"type": "frame", "ts": f.ts, "kind": f.kind, "hex": f.raw.hex()}) + "\n")
            tx = tracker.push(f)
            if tx is None:
                continue
            if jsonl:
                jsonl.write(json.dumps({"type": "tx", "ts": tx.ts, "addr": tx.addr, "fc": tx.fc,
                                        "op": tx.op, "start": tx.start, "values": tx.values}) + "\n")
                jsonl.flush()
            rmap = maps.get(tx.addr, RegisterMap.empty())
            label = "WRITE" if tx.op == "write" else "read "
            print(f"  {label} slave {tx.addr} fc{tx.fc} @ {tx.start:#06x} x{len(tx.values)}")
            for addr, name, value in rmap.decode_block(tx.start, tx.values):
                print(f"    {addr:#06x} {name:<32} {value}")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
