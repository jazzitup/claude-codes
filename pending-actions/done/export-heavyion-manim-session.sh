#!/bin/bash
# One-shot pending action (runs on every SessionStart on every Mac via
# scripts/session-start-setup.sh until done):
# find the local Claude Code session(s) that made
#   "2026.10.08 서울대 세미나/HeavyIon_PbPb_5TeV_30-50_manim_*.mp4"
# (hic_scene.py / hic_scene_v2.py, 2026-10-25 and 2026-10-29) and append their
# full transcripts to the Dropbox log next to the video:
#   claude_session_log_2026-11-04.md   (another session already writes its own
#   notes there, so we only APPEND one marked section)  +  raw .jsonl copies.
# Requested 2026-11-04. Idempotent: exits at once if the marker is already in the .md.
# Move this file to pending-actions/done/ once the export has been confirmed.
DEST_DIR="$HOME/Library/CloudStorage/Dropbox/My transparencies/2026.10.08 서울대 세미나"
TARGET="$DEST_DIR/claude_session_log_2026-11-04.md"
MARKER="<!-- heavyion-manim-session-export -->"
LOG=/tmp/claude-pending-actions.log

[ -d "$DEST_DIR" ] || exit 0
[ -f "$TARGET" ] && grep -qF "$MARKER" "$TARGET" && exit 0

python3 - "$TARGET" "$DEST_DIR" "$MARKER" <<'PY' >>"$LOG" 2>&1
import json, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

target, dest_dir, marker = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
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

found = [p for p in sorted(Path.home().glob(".claude/projects/*/*.jsonl"))
         if p.stem != SKIP_SESSION and hit(p)]
if not found:
    sys.exit(0)

renderer = Path.home() / "claude-codes/scripts/session-jsonl-to-md.py"
tmp = Path(tempfile.mkstemp(suffix=".md")[1])
subprocess.run([sys.executable, str(renderer), str(tmp), *map(str, found)], check=True)
body = tmp.read_text(encoding="utf-8")
tmp.unlink()

copies = []
for p in found:
    dst = dest_dir / f"claude_session_log_2026-11-04_{p.stem[:8]}.jsonl"
    shutil.copy2(p, dst)
    copies.append(dst.name)

section = (
    f"\n\n---\n\n{marker}\n"
    f"# heavy-ion manim 영상(HeavyIon_PbPb_5TeV_30-50_manim_*)을 만든 세션 로그 — 자동 복사 "
    f"{datetime.now():%Y-%m-%d %H:%M}\n\n"
    f"`~/claude-codes/pending-actions/export-heavyion-manim-session.sh` 가 이 Mac 의 "
    f"`~/.claude/projects` 에서 찾아 붙인 것. 원본 jsonl 복사본: " + ", ".join(f"`{c}`" for c in copies) + "\n\n"
    + body
)
with target.open("a", encoding="utf-8") as f:
    f.write(section)
print(datetime.now().isoformat(), "exported", [str(p) for p in found], "->", target)
PY
exit 0
