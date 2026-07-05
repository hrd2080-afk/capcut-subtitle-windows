#!/usr/bin/env python3
"""Transcribe audio to word-level timestamps with faster-whisper.

Music defeats Whisper two ways:
1. VAD drops sung vocals as "non-speech" -> VAD is OFF.
2. On long tracks the decoder skips spans, so we transcribe in overlapping
   windows AND run a gap-fill pass to recover missed spans.

Usage:
  transcribe.py <audio.wav> <out.json> [--model medium] [--lang ko]
                [--window 30] [--hop 28] [--gap 6]
"""

import argparse
import json
import sys


def transcribe_chunk(model, audio, SR, lang, t0, t1):
    chunk = audio[int(t0 * SR):int(t1 * SR)]
    segments, _ = model.transcribe(
        chunk, language=lang, word_timestamps=True, beam_size=5,
        vad_filter=False, condition_on_previous_text=False)
    words, segs = [], []
    for s in segments:
        segs.append({"start": t0 + s.start, "end": t0 + s.end, "text": s.text})
        for w in (s.words or []):
            words.append({"start": t0 + w.start, "end": t0 + w.end, "word": w.word})
    return words, segs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--model", default="medium")
    ap.add_argument("--lang", default="ko")
    ap.add_argument("--window", type=float, default=30.0)
    ap.add_argument("--hop", type=float, default=28.0)
    ap.add_argument("--gap", type=float, default=6.0,
                    help="re-transcribe word-gaps longer than this (s)")
    args = ap.parse_args()

    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio

    SR = 16000
    audio = decode_audio(args.audio, sampling_rate=SR)
    total_s = len(audio) / SR
    model = WhisperModel(args.model, device="cpu", compute_type="int8")

    # ---- pass 1: overlapping windows ------------------------------------
    words, seg_list = [], []
    seen_until = 0.0
    start = 0.0
    while start < total_s:
        end = min(start + args.window, total_s)
        w, s = transcribe_chunk(model, audio, SR, args.lang, start, end)
        is_last = end >= total_s
        keep_until = total_s if is_last else start + args.hop
        for seg in s:
            if seg["start"] < seen_until - 0.01:
                continue
            seg_list.append(seg)
            print(f"  [{seg['start']:6.1f}s] {seg['text']}", file=sys.stderr)
        for wd in w:
            if seen_until - 0.01 <= wd["start"] < keep_until:
                words.append(wd)
        seen_until = keep_until
        start += args.hop

    words.sort(key=lambda x: x["start"])

    # ---- pass 2: gap-fill (re-transcribe spans with no words) -----------
    PAD = 1.5
    bounds = [0.0] + [w["start"] for w in words] + [total_s]
    spans = []
    for i in range(len(bounds) - 1):
        g0 = bounds[i] if i == 0 else words[i - 1]["end"]
        g1 = bounds[i + 1]
        if g1 - g0 > args.gap:
            spans.append((max(0.0, g0 - PAD), min(total_s, g1 + PAD), g0, g1))

    for s0, s1, g0, g1 in spans:
        fw, fs = transcribe_chunk(model, audio, SR, args.lang, s0, s1)
        added = 0
        for wd in fw:
            if g0 - 0.2 < wd["start"] < g1 + 0.2:
                words.append(wd)
                added += 1
        for seg in fs:
            if g0 - 0.2 < seg["start"] < g1 + 0.2:
                seg_list.append(seg)
        if added:
            print(f"  gap-fill [{g0:6.1f}-{g1:6.1f}s] +{added} words", file=sys.stderr)

    words.sort(key=lambda x: x["start"])
    seg_list.sort(key=lambda x: x["start"])

    out = {"language": args.lang, "duration": total_s,
           "segments": seg_list, "words": words}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\n{len(words)} words over {total_s:.0f}s -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
