#!/usr/bin/env python3
"""Build a CapCut draft (video + auto subtitles) from a cue list.

Strategy: clone proven objects from an existing, known-good project:
* content template (a real draft_info.json) supplies the text style,
  per-segment companion materials, and track skeleton;
* scaffold folder supplies the auxiliary files CapCut expects.

Templates are bundled with the skill (engine/templates/).

Usage:
  build_draft.py --video <abs.mp4> --cues cues.json --name "draft name"
                 [--root <CapCut com.lveditor.draft path>]

Windows default CapCut draft path:
  %LOCALAPPDATA%\\CapCut\\User Data\\Projects\\com.lveditor.draft
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from copy import deepcopy

US = 1_000_000
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "templates")


def _default_capcut_root():
    """Return the CapCut draft root for the current platform."""
    if sys.platform == "win32":
        local_app = os.environ.get("LOCALAPPDATA", "")
        return os.path.join(local_app, "CapCut", "User Data",
                            "Projects", "com.lveditor.draft")
    # macOS fallback
    return os.path.expanduser(
        "~/Movies/CapCut/User Data/Projects/com.lveditor.draft")


DEFAULT_ROOT = _default_capcut_root()


def uid() -> str:
    return str(uuid.uuid4()).upper()


def probe(video):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-show_entries", "format=duration",
        "-of", "json", video]).decode()
    j = json.loads(out)
    w = int(j["streams"][0]["width"])
    h = int(j["streams"][0]["height"])
    dur_us = int(round(float(j["format"]["duration"]) * US))
    return w, h, dur_us


def id_index(materials):
    idx = {}
    for name, arr in materials.items():
        if isinstance(arr, list):
            for it in arr:
                if isinstance(it, dict) and "id" in it:
                    idx[it["id"]] = (name, it)
    return idx


def find_track(info, ttype):
    for t in info["tracks"]:
        if t["type"] == ttype:
            return t
    raise SystemExit(f"template has no {ttype} track")


def build(video, cues, name, tpl_info, tpl_meta, scaffold, root):
    W, H, DUR = probe(video)
    base = json.load(open(tpl_info, encoding="utf-8"))
    idx = id_index(base["materials"])

    vtrack_tpl = find_track(base, "video")
    vseg_tpl = vtrack_tpl["segments"][0]
    vmat_name, vmat_tpl = idx[vseg_tpl["material_id"]]

    ttrack_tpl = find_track(base, "text")
    tseg_tpl = ttrack_tpl["segments"][0]
    tmat_name, tmat_tpl = idx[tseg_tpl["material_id"]]
    anim_name, anim_tpl = idx[tseg_tpl["extra_material_refs"][0]]

    mats = {}
    for k, v in base["materials"].items():
        mats[k] = [] if isinstance(v, list) else deepcopy(v)

    # ---- video material --------------------------------------------------
    nv = deepcopy(vmat_tpl)
    nv["id"] = uid()
    nv["path"] = os.path.abspath(video)
    nv["media_path"] = os.path.abspath(video)
    nv["material_name"] = os.path.basename(video)
    nv["width"], nv["height"], nv["duration"] = W, H, DUR
    nv["has_audio"] = True
    mats[vmat_name].append(nv)

    new_refs = []
    for rid in vseg_tpl["extra_material_refs"]:
        lname, comp = idx[rid]
        nc = deepcopy(comp)
        nc["id"] = uid()
        mats[lname].append(nc)
        new_refs.append(nc["id"])

    nvs = deepcopy(vseg_tpl)
    nvs["id"] = uid()
    nvs["material_id"] = nv["id"]
    nvs["extra_material_refs"] = new_refs
    nvs["source_timerange"] = {"start": 0, "duration": DUR}
    nvs["target_timerange"] = {"start": 0, "duration": DUR}
    nvs["speed"] = 1.0
    nvs["clip"] = {"scale": {"x": 1.0, "y": 1.0}, "rotation": 0.0,
                   "transform": {"x": 0.0, "y": 0.0},
                   "flip": {"vertical": False, "horizontal": False}, "alpha": 1.0}

    # ---- text materials (one per cue) ------------------------------------
    text_segs = []
    for i, cue in enumerate(cues):
        tm = deepcopy(tmat_tpl)
        tm["id"] = uid()
        content = json.loads(tm["content"])
        content["text"] = cue["text"]

        # Clear macOS-specific font paths; CapCut will use its default font.
        for st in content.get("styles", []):
            st["range"] = [0, len(cue["text"])]
            if "font" in st:
                st["font"]["path"] = ""
                st["font"]["id"] = ""

        tm["content"] = json.dumps(content, ensure_ascii=False)
        # Clear macOS font_path at top level
        tm["font_path"] = ""
        tm["font_id"] = ""
        mats[tmat_name].append(tm)

        anim = deepcopy(anim_tpl)
        anim["id"] = uid()
        mats[anim_name].append(anim)

        ts = deepcopy(tseg_tpl)
        ts["id"] = uid()
        ts["material_id"] = tm["id"]
        ts["extra_material_refs"] = [anim["id"]]
        ts["source_timerange"] = None
        ts["target_timerange"] = {"start": int(cue["start_us"]),
                                  "duration": int(cue["dur_us"])}
        ts["render_index"] = 14000 + i
        text_segs.append(ts)

    # ---- assemble tracks + top-level -------------------------------------
    vtrack = deepcopy(vtrack_tpl)
    vtrack["id"] = uid()
    vtrack["segments"] = [nvs]

    ttrack = deepcopy(ttrack_tpl)
    ttrack["id"] = uid()
    ttrack["segments"] = text_segs

    info = deepcopy(base)
    info["materials"] = mats
    info["tracks"] = [vtrack, ttrack]
    info["id"] = uid()
    info["duration"] = DUR
    info["name"] = ""
    info["canvas_config"] = {"ratio": "original", "width": W, "height": H,
                             "background": None}
    info["create_time"] = 0
    info["update_time"] = 0
    # Mark platform as Windows
    for pkey in ("platform", "last_modified_platform"):
        if pkey in info and isinstance(info[pkey], dict):
            info[pkey]["os"] = "windows"

    # ---- meta ------------------------------------------------------------
    now_us = int(time.time() * US)
    fold = os.path.join(root, name)
    meta = json.load(open(tpl_meta, encoding="utf-8"))
    meta["draft_name"] = name
    meta["draft_fold_path"] = fold
    meta["draft_root_path"] = root
    meta["draft_id"] = uid()
    meta["tm_draft_create"] = now_us
    meta["tm_draft_modified"] = now_us
    meta["tm_duration"] = DUR

    vitem_tpl = None
    for entry in meta.get("draft_materials", []):
        if entry.get("type") == 0 and entry.get("value"):
            vitem_tpl = entry["value"][0]
            break

    for entry in meta.get("draft_materials", []):
        if entry.get("type") == 0 and vitem_tpl is not None:
            vi = deepcopy(vitem_tpl)
            vi["id"] = str(uuid.uuid4())
            vi["file_Path"] = os.path.abspath(video)
            vi["extra_info"] = os.path.basename(video)
            vi["width"], vi["height"], vi["duration"] = W, H, DUR
            vi["create_time"] = int(time.time())
            vi["import_time"] = int(time.time())
            vi["import_time_ms"] = now_us
            vi["md5"] = ""
            entry["value"] = [vi]
        else:
            entry["value"] = []

    # ---- write folder ----------------------------------------------------
    if os.path.exists(fold):
        bak = fold + f".bak-{int(time.time())}"
        shutil.move(fold, bak)
        print(f"existing folder backed up -> {bak}")

    os.makedirs(fold)

    for fn in ("draft_agency_config.json", "draft_settings",
               "draft_biz_config.json", "timeline_layout.json"):
        src = os.path.join(scaffold, fn)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(fold, fn))

    json.dump({"draft_materials": [], "draft_virtual_store": []},
              open(os.path.join(fold, "draft_virtual_store.json"),
                   "w", encoding="utf-8"))

    for d in ("adjust_mask", "common_attachment", "matting", "qr_upload",
              "smart_crop", "subdraft", "Resources", "Timelines"):
        os.makedirs(os.path.join(fold, d), exist_ok=True)

    with open(os.path.join(fold, "draft_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False)

    shutil.copyfile(os.path.join(fold, "draft_info.json"),
                    os.path.join(fold, "draft_info.json.bak"))

    with open(os.path.join(fold, "draft_meta_info.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)

    print(f"draft created: {fold}")
    print(f"  video {W}x{H} {DUR/US:.1f}s  subtitles: {len(cues)} cues")
    return fold


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--cues", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--template-info",
                    default=os.path.join(TEMPLATES, "draft_info.json"))
    ap.add_argument("--template-meta",
                    default=os.path.join(TEMPLATES, "draft_meta_info.json"))
    ap.add_argument("--scaffold",
                    default=os.path.join(TEMPLATES, "scaffold"))
    ap.add_argument("--root", default=DEFAULT_ROOT)
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        if sys.platform == "win32":
            hint = (
                f"CapCut 드래프트 폴더를 찾을 수 없습니다:\n  {args.root}\n"
                "CapCut을 한 번 실행해 폴더를 생성하거나, "
                "--root 옵션으로 직접 경로를 지정하세요.\n"
                "일반적인 Windows 경로:\n"
                r"  %LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft"
            )
        else:
            hint = (
                f"CapCut draft folder not found:\n  {args.root}\n"
                "Open CapCut at least once to create this folder, "
                "or pass --root <your CapCut drafts path>."
            )
        raise SystemExit(hint)

    cues = json.load(open(args.cues, encoding="utf-8"))["cues"]
    build(args.video, cues, args.name,
          args.template_info, args.template_meta,
          args.scaffold, args.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
