#!/usr/bin/env python3
"""cues.json -> .srt (universal subtitle format)."""

import argparse
import json


def ts(us: int) -> str:
    ms = us // 1000
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cues")
    ap.add_argument("out")
    args = ap.parse_args()

    cues = json.load(open(args.cues, encoding="utf-8"))["cues"]
    lines = []
    for i, c in enumerate(cues, 1):
        start = int(c["start_us"])
        end = start + int(c["dur_us"])
        lines.append(f"{i}\n{ts(start)} --> {ts(end)}\n{c['text']}\n")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"{len(cues)} cues -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
