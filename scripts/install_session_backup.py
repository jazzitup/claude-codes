#!/usr/bin/env python3
"""Idempotent: make this Mac back up Claude Code transcripts to GitHub at SessionEnd.
Copies scripts/backup-sessions.sh to ~/.claude/scripts/, clones jazzitup/claude-sessions
to ~/claude-sessions if missing, registers the SessionEnd hook, and sets
cleanupPeriodDays so local transcripts are never auto-deleted."""
import json, os, shutil, subprocess

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO_DIR, "scripts", "backup-sessions.sh")
DEST = os.path.expanduser("~/.claude/scripts/backup-sessions.sh")
SESS = os.path.expanduser("~/claude-sessions")
SETTINGS = os.path.expanduser("~/.claude/settings.json")

os.makedirs(os.path.dirname(DEST), exist_ok=True)
if not os.path.exists(DEST) or open(SRC, "rb").read() != open(DEST, "rb").read():
    shutil.copyfile(SRC, DEST)
os.chmod(DEST, 0o755)

if not os.path.isdir(os.path.join(SESS, ".git")):
    subprocess.run(["git", "clone", "--quiet", "https://github.com/jazzitup/claude-sessions.git", SESS],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)

s = json.load(open(SETTINGS, encoding="utf-8")) if os.path.isfile(SETTINGS) else {}
changed = False
groups = s.setdefault("hooks", {}).setdefault("SessionEnd", [])
if not any("backup-sessions.sh" in h.get("command", "") for g in groups for h in g.get("hooks", [])):
    groups.append({"hooks": [{"type": "command", "command": "~/.claude/scripts/backup-sessions.sh",
                              "timeout": 60, "async": True,
                              "statusMessage": "Backing up session to GitHub..."}]})
    changed = True
if (s.get("cleanupPeriodDays") or 0) < 36500:
    s["cleanupPeriodDays"] = 36500
    changed = True
if changed:
    with open(SETTINGS, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2); f.write("\n")
