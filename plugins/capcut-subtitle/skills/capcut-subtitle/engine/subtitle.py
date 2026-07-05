#!/usr/bin/env python3
"""One-shot CapCut auto-subtitle pipeline.

video (+ optional script) -> CapCut draft with timed, styled subtitles

Stages: extract audio (ffmpeg) -> transcribe word timings (faster-whisper)
-> build cues (align to script, or use transcription) -> SRT -> CapCut draft
(cloned from a real draft so it opens natively).

Usage:
  subtitle.py --video <path.mp4> [--script <lyrics.txt>] [--name <draft>]
              [--model medium] [--lang ko]
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
US = 1_000_000


def run(*cmd):
    print("›", " ".join(str(c) for c in cmd[:2]), "…")
    subprocess.run([str(c) for c in cmd], check=True)


def probe_duration(video):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nokey=1:noprint_wrappers=1", video]).decode().strip()
    return float(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--script", default=None,
                    help="script/lyrics; omit for pure auto-transcription")
    ap.add_argument("--name", default=None,
                    help="CapCut draft name (default: video filename)")
    ap.add_argument("--model", default="medium")
    ap.add_argument("--lang", default="ko")
    ap.add_argument("--workdir",
                    default=os.path.join(os.path.expanduser("~"),
                                         ".capcut-subtitle", "work"))
    args = ap.parse_args()

    video = os.path.abspath(args.video)
    if not os.path.exists(video):
        raise SystemExit(f"video not found: {video}")

    name = args.name or os.path.splitext(os.path.basename(video))[0]
    work = os.path.join(os.path.abspath(args.workdir), name)
    os.makedirs(work, exist_ok=True)

    wav = os.path.join(work, "audio.wav")
    words = os.path.join(work, "words.json")
    cues = os.path.join(work, "cues.json")
    srt = os.path.join(work, "subs.srt")
    report = os.path.join(work, "verify.json")

    dur = probe_duration(video)

    # 1. audio
    run("ffmpeg", "-y", "-i", video, "-ac", "1", "-ar", "16000", "-vn",
        "-c:a", "pcm_s16le", wav)

    # 2. transcribe
    run(PY, os.path.join(HERE, "transcribe.py"), wav, words,
        "--model", args.model, "--lang", args.lang)

    # 3. cues
    align_cmd = [PY, os.path.join(HERE, "align.py"),
                 "--words", words, "--out", cues, "--duration", dur]
    if args.script:
        align_cmd += ["--script", os.path.abspath(args.script)]
    run(*align_cmd)

    # 4. sync check
    verify = subprocess.run(
        [PY, os.path.join(HERE, "verify.py"),
         "--cues", cues, "--words", words, "--report", report])

    # 5. srt
    run(PY, os.path.join(HERE, "to_srt.py"), cues, srt)

    # 6. draft
    run(PY, os.path.join(HERE, "build_draft.py"),
        "--video", video, "--cues", cues, "--name", name)

    n = len(json.load(open(cues, encoding="utf-8"))["cues"])
    print(f"\n✓ done — {n} subtitles, {dur:.0f}s")
    print(f"  draft name: {name}")
    print(f"  srt: {srt} | sync report: {report}")

    if verify.returncode == 2:
        print("  ⚠ some cues flagged low-sync — see report; "
              "consider --model large-v3 for a redo.")
    print("  CapCut을 열어 새로 생긴 드래프트를 확인하세요 "
          "(목록에 없으면 CapCut 재시작).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
