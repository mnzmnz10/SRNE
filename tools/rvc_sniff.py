#!/usr/bin/env python3
"""Passive CAN / RV-C sniffer for the SRNE bus.

Inputs:
  --esp32 PORT     ESP32 CAN sniffer firmware (firmware/esp32-can-sniffer), lines 'C <ms> <id> <data>'
  --candump FILE   Linux `candump -L can0` log, lines '(ts) can0 18FFFD80#0102...'
  --socketcan IF   live SocketCAN interface via python-can (e.g. a USB-CAN adapter)

  python tools/rvc_sniff.py --esp32 /dev/ttyUSB0 --log cap.candump
  python tools/rvc_sniff.py --candump cap.candump --summary
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from srne.rvc import RvcFrame, decode  # noqa: E402


def from_esp32_lines(lines):
    for line in lines:
        if isinstance(line, bytes):
            line = line.decode("ascii", "replace")
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "C":
            yield RvcFrame(int(parts[1]) / 1000, int(parts[2], 16), bytes.fromhex("".join(parts[3:])))
        elif line.strip():
            print(f"# {line.strip()}", file=sys.stderr)


def from_candump(lines):
    for line in lines:
        parts = line.split()
        if len(parts) < 3 or "#" not in parts[2]:
            continue
        can_id, _, data = parts[2].partition("#")
        yield RvcFrame(float(parts[0].strip("()")), int(can_id, 16), bytes.fromhex(data))


def from_socketcan(channel: str):
    import can

    with can.Bus(interface="socketcan", channel=channel) as bus:
        for msg in bus:
            if msg.is_extended_id:
                yield RvcFrame(msg.timestamp, msg.arbitration_id, bytes(msg.data))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--esp32")
    src.add_argument("--candump")
    src.add_argument("--socketcan")
    ap.add_argument("--log", help="save frames in candump -L format for later replay")
    ap.add_argument("--summary", action="store_true",
                    help="print only a per-DGN/source table at the end (which bytes change)")
    args = ap.parse_args()

    if args.esp32:
        import serial

        ser = serial.Serial(args.esp32, 921600)
        frames = from_esp32_lines(iter(ser.readline, b""))
    elif args.candump:
        frames = from_candump(open(args.candump, encoding="ascii", errors="replace"))
    else:
        frames = from_socketcan(args.socketcan)

    log = open(args.log, "a", encoding="ascii") if args.log else None
    seen: dict[tuple[int, int], list[bytes]] = defaultdict(list)
    try:
        for f in frames:
            if log:
                log.write(f"({f.ts:.6f}) can0 {f.can_id:08X}#{f.data.hex().upper()}\n")
                log.flush()
            if args.summary:
                seen[(f.dgn, f.source)].append(f.data)
                continue
            fields = decode(f)
            text = " ".join(f"{k}={v}" for k, v in fields.items()) if fields else ""
            print(f"{f.ts:10.3f} src={f.source:02X} {f.name:<24} {f.data.hex(' '):<24} {text}")
    except KeyboardInterrupt:
        pass

    if args.summary:
        print(f"{'DGN':<26}{'src':>4}{'count':>7}  changing bytes / last data")
        for (dgn, src), datas in sorted(seen.items()):
            name = RvcFrame(0, (dgn << 8) | src, b"").name
            n = max(len(d) for d in datas)
            changing = [i for i in range(n) if len({d[i] for d in datas if len(d) > i}) > 1]
            print(f"{name:<26}{src:>4X}{len(datas):>7}  {changing}  {datas[-1].hex(' ')}")


if __name__ == "__main__":
    main()
