#!/usr/bin/env python3
"""Summarises a sniffer JSONL capture to help map unknown registers.

For every (slave, function, register) it shows how often it was polled and
how its value moved. Registers that track something you can change on
purpose (turn on a load, cover the panels, start the engine for the DC-DC)
stand out in the "distinct" and min/max columns.

  python tools/analyze.py cap.jsonl
  python tools/analyze.py cap.jsonl --slave 1 --writes
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jsonl")
    ap.add_argument("--slave", type=lambda s: int(s, 0))
    ap.add_argument("--writes", action="store_true", help="list every write the master sent")
    args = ap.parse_args()

    stats: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    kinds: dict[str, int] = defaultdict(int)
    polls: dict[tuple[int, int, int, int], int] = defaultdict(int)
    writes = []

    with open(args.jsonl, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec["type"] == "frame":
                kinds[rec["kind"]] += 1
                continue
            if args.slave is not None and rec["addr"] != args.slave:
                continue
            if rec["op"] == "write":
                writes.append(rec)
            else:
                polls[(rec["addr"], rec["fc"], rec["start"], len(rec["values"]))] += 1
            for i, v in enumerate(rec["values"]):
                stats[(rec["addr"], rec["fc"], rec["start"] + i)].append(v)

    print("Frame kinds:", dict(kinds))
    print("\nPoll blocks (slave, fc, start, count): times")
    for (addr, fc, start, count), n in sorted(polls.items()):
        print(f"  slave {addr:<3} fc{fc} {start:#06x} x{count:<3} {n}")

    print(f"\n{'slave':>5} {'fc':>3} {'reg':>7} {'n':>6} {'distinct':>8} {'min':>7} {'max':>7} {'last':>7}")
    for (addr, fc, reg), vals in sorted(stats.items()):
        print(f"{addr:>5} {fc:>3} {reg:#07x} {len(vals):>6} {len(set(vals)):>8} "
              f"{min(vals):>7} {max(vals):>7} {vals[-1]:>7}")

    if args.writes:
        print("\nWrites:")
        for w in writes:
            print(f"  {w['ts']:.3f} slave {w['addr']} fc{w['fc']} {w['start']:#06x} = {w['values']}")


if __name__ == "__main__":
    main()
