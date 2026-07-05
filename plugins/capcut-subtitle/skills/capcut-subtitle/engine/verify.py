#!/usr/bin/env python3
"""Self-check subtitle sync without a GUI.

For each cue, collect words Whisper heard during the on-screen window and
fuzzy-compare to the cue text. Low match scores are flagged as suspect.

Exit code 0 if all cues pass, 2 if any suspect cues remain.

Usage:
  verify.py --cues cues.json --words words.json [--threshold 0.45] [--pad 0.4]
"""

import argparse
import json
import re
from difflib import SequenceMatcher

US = 1_000_000


def norm(s):
    return re.sub(r"[^0-9a-z가-힣]", "", s.lower())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cues", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--threshold", type=float, default=0.45)
    ap.add_argument("--pad", type=float, default=0.4)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    cues = json.load(open(args.cues, encoding="utf-8"))["cues"]
    words = json.load(open(args.words, encoding="utf-8"))["words"]

    rows = []
    for c in cues:
        s = c["start_us"] / US
        e = s + c["dur_us"] / US
        heard = "".join(norm(w["word"]) for w in words
                        if s - args.pad <= w["start"] < e + args.pad)
        want = norm(c["text"])
        ratio = SequenceMatcher(None, want, heard).ratio() if heard else 0.0
        rows.append({"start_us": c["start_us"], "dur_us": c["dur_us"],
                     "text": c["text"], "score": round(ratio, 2),
                     "heard": heard})

    suspects = [r for r in rows if r["score"] < args.threshold]
    avg = sum(r["score"] for r in rows) / len(rows) if rows else 0.0
    print(f"avg sync score: {avg:.2f} | {len(rows)-len(suspects)}/{len(rows)} ok "
          f"| {len(suspects)} suspect (<{args.threshold})")
    for r in suspects:
        print(f"  ⚠ {r['start_us']/US:6.2f}s score={r['score']:.2f} "
              f"want={r['text']!r} heard≈{r['heard'][:24]!r}")

    if args.report:
        json.dump({"avg": avg, "rows": rows, "suspects": suspects},
                  open(args.report, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    return 0 if not suspects else 2


if __name__ == "__main__":
    raise SystemExit(main())
