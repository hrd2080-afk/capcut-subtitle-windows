#!/usr/bin/env python3
"""Turn Whisper word timings into well-formed subtitle cues.

Two modes:
* with --script: the script/lyrics are authoritative text; globally aligned
  to Whisper's word timings (Needleman-Wunsch).
* without --script: Whisper's own transcription used as cues.

Both feed the same cleaning pass: monotonic, non-overlapping cues with sane
min/max durations (CapCut rejects overlaps).

Output (json): {"cues": [{"start_us", "dur_us", "text", "matched"}]}
"""

import argparse
import json
import re
from difflib import SequenceMatcher

US = 1_000_000
MIN_DUR = 0.7
MAX_DUR = 7.0
MIN_GAP = 0.04


def norm(s: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", s.lower())


def load_script(path: str):
    lines = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            t = raw.strip()
            if not t or (t.startswith("[") and t.endswith("]")):
                continue
            words = [norm(w) for w in t.split() if norm(w)]
            if words:
                lines.append((t, words))
    return lines


def needleman_wunsch(a, b, gap=-0.5):
    n, m = len(a), len(b)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * gap
    for j in range(1, m + 1):
        dp[0][j] = j * gap
    for i in range(1, n + 1):
        ai = a[i - 1]
        row, prev = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            ratio = SequenceMatcher(None, ai, b[j - 1]).ratio()
            row[j] = max(prev[j - 1] + (2 * ratio - 1),
                         prev[j] + gap, row[j - 1] + gap)
    pairs = []
    i, j = n, m
    while i > 0 and j > 0:
        ratio = SequenceMatcher(None, a[i - 1], b[j - 1]).ratio()
        if dp[i][j] == dp[i - 1][j - 1] + (2 * ratio - 1):
            pairs.append((i - 1, j - 1)); i -= 1; j -= 1
        elif dp[i][j] == dp[i - 1][j] + gap:
            pairs.append((i - 1, None)); i -= 1
        else:
            pairs.append((None, j - 1)); j -= 1
    while i > 0:
        pairs.append((i - 1, None)); i -= 1
    while j > 0:
        pairs.append((None, j - 1)); j -= 1
    pairs.reverse()
    return pairs


def raw_from_script(wwords, script_path, media_dur):
    script_lines = load_script(script_path)
    flat, line_of = [], []
    for li, (_, words) in enumerate(script_lines):
        for w in words:
            flat.append(w); line_of.append(li)
    wnorm = [norm(w["word"]) for w in wwords]
    pairs = needleman_wunsch(flat, wnorm)
    n = len(script_lines)
    starts = [None] * n
    ends = [None] * n
    matched = [0] * n
    for i, j in pairs:
        if i is None or j is None:
            continue
        if SequenceMatcher(None, flat[i], wnorm[j]).ratio() < 0.34:
            continue
        li = line_of[i]
        st, en = wwords[j]["start"], wwords[j]["end"]
        if starts[li] is None or st < starts[li]:
            starts[li] = st
        if ends[li] is None or en > ends[li]:
            ends[li] = en
        matched[li] += 1
    counts = [len(script_lines[i][1]) for i in range(n)]
    known = [i for i in range(n) if starts[i] is not None]
    if not known:
        raise SystemExit("alignment failed: no lines matched any audio")

    def fill(lo, hi, t0, t1):
        total = sum(counts[lo:hi]) or 1
        acc = 0
        for i in range(lo, hi):
            starts[i] = t0 + (t1 - t0) * acc / total
            acc += counts[i]
            ends[i] = t0 + (t1 - t0) * acc / total

    first, last = known[0], known[-1]
    if first > 0:
        fill(0, first, 0.0, starts[first])
    if last < n - 1:
        tail = media_dur if media_dur else ends[last] + sum(counts[last + 1:]) * 0.4
        fill(last + 1, n, ends[last], tail)
    for k in range(len(known) - 1):
        a, b = known[k], known[k + 1]
        if b - a > 1:
            fill(a + 1, b, ends[a], starts[b])
    for i in range(n):
        if ends[i] is None:
            ends[i] = starts[i] + max(MIN_DUR, counts[i] * 0.35)
    return [{"text": script_lines[i][0], "start": max(0.0, starts[i]),
             "end": max(0.0, ends[i]), "matched": matched[i]} for i in range(n)]


def raw_from_whisper(wdata):
    raw = [{"text": s["text"].strip(), "start": s["start"], "end": s["end"],
            "matched": 1} for s in wdata["segments"] if s["text"].strip()]
    if not raw:
        raise SystemExit("no speech recognized")
    return raw


def emit_cues(raw, media_dur, out_path):
    raw.sort(key=lambda c: c["start"])
    GAP = max(2, int(MIN_GAP * 1000))
    MIN_MS, MAX_MS = int(MIN_DUR * 1000), int(MAX_DUR * 1000)
    dur_ms = int(media_dur * 1000) if media_dur else None
    starts = [int(round(c["start"] * 1000)) for c in raw]
    prev_end = -GAP
    out = []
    n = len(raw)
    for idx, c in enumerate(raw):
        start = max(starts[idx], prev_end + GAP)
        ceil_end = (starts[idx + 1] - GAP if idx + 1 < n
                    else (dur_ms or start + MAX_MS))
        end = min(max(start + MIN_MS, int(round(c["end"] * 1000))), start + MAX_MS)
        if end > ceil_end:
            end = ceil_end
        if end <= start:
            end = start + GAP
        if dur_ms:
            end = min(end, dur_ms)
        prev_end = end
        out.append({"start_us": start * 1000, "dur_us": (end - start) * 1000,
                    "text": c["text"], "matched": c["matched"]})
    json.dump({"cues": out}, open(out_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    anchored = sum(1 for c in out if c["matched"] > 0)
    print(f"{len(out)} cues ({anchored} audio-anchored, "
          f"{len(out) - anchored} interpolated) -> {out_path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", required=True)
    ap.add_argument("--script", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=None)
    args = ap.parse_args()

    wdata = json.load(open(args.words, encoding="utf-8"))
    media_dur = args.duration or wdata.get("duration")
    if args.script:
        wwords = [w for w in wdata["words"] if norm(w["word"])]
        raw = raw_from_script(wwords, args.script, media_dur)
    else:
        raw = raw_from_whisper(wdata)
    emit_cues(raw, media_dur, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
