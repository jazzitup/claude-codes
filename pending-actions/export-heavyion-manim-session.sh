#!/bin/bash
# One-shot pending action (runs on every SessionStart on every Mac via
# scripts/session-start-setup.sh until the target file exists):
# find the local Claude Code session(s) that made
#   "2026.10.08 서울대 세미나/HeavyIon_PbPb_5TeV_30-50_manim_*.mp4"
# (hic_scene.py / hic_scene_v2.py, 2026-10-25 and 2026-10-29) and copy their
# full transcripts into the Dropbox folder next to the video:
#   claude_session_log_2026-11-04.md  (readable)  +  raw .jsonl copies.
# Requested 2026-11-04. Idempotent: exits at once if the .md already exists.
# Move this file to pending-actions/done/ once the export has been confirmed.
DEST_DIR="$HOME/Library/CloudStorage/Dropbox/My transparencies/2026.10.08 서울대 세미나"
TARGET="$DEST_DIR/claude_session_log_2026-11-04.md"
LOG=/tmp/claude-pending-actions.log

[ -e "$TARGET" ] && exit 0
[ -d "$DEST_DIR" ] || exit 0

python3 - "$TARGET" "$DEST_DIR" <<'PY' >>"$LOG" 2>&1
import json, shutil, subprocess, sys
from pathlib import Path

target, dest_dir = Path(sys.argv[1]), Path(sys.argv[2])
KEYS = ("hic_scene", "heavy_ion_manim", "HeavyIon_PbPb_5TeV")
SKIP_SESSION = "c29f5186-09b3-4fb2-b6af-5fd973f8025c"   # MacBook-Pro-2 session that only searched for the log
CUTOFF = "2026-11-01"                                     # real work was 2026-10-25 / 2026-10-29

def hit(path):
    """True if a keyword appears on a timestamped line dated before CUTOFF."""
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if not any(k in line for k in KEYS):
                continue
            try:
                ts = json.loads(line).get("timestamp") or ""
            except ValueError:
                continue
            if ts and ts[:10] < CUTOFF:
                return True
    return False

found = []
for p in sorted(Path.home().glob(".claude/projects/*/*.jsonl")):
    if p.stem == SKIP_SESSION:
        continue
    if hit(p):
        found.append(p)
if not found:
    sys.exit(0)

renderer = Path.home() / "claude-codes/scripts/session-jsonl-to-md.py"
subprocess.run([sys.executable, str(renderer), str(target), *map(str, found)], check=True)
for p in found:
    shutil.copy2(p, dest_dir / f"claude_session_log_2026-11-04_{p.stem[:8]}.jsonl")
print("exported", [str(p) for p in found], "->", target)
PY
exit 0
