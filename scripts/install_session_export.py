#!/usr/bin/env python3
"""Idempotently install the session-export hooks into ~/.claude/settings.json
and copy scripts/session_export.py from this repo into ~/.claude/scripts/.
Safe to run on every session start (mac-shortcuts-style auto install)."""
import json
import os
import shutil

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_SCRIPT = os.path.join(REPO_DIR, "scripts", "session_export.py")
DEST_SCRIPT = os.path.expanduser("~/.claude/scripts/session_export.py")
SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")

BACKFILL_CMD = f'python3 "{DEST_SCRIPT}" backfill 2>/dev/null || true'
SESSION_CMD = f'python3 "{DEST_SCRIPT}" session 2>/dev/null || true'


def install_script():
    os.makedirs(os.path.dirname(DEST_SCRIPT), exist_ok=True)
    if not os.path.isfile(DEST_SCRIPT) or not files_equal(SRC_SCRIPT, DEST_SCRIPT):
        shutil.copyfile(SRC_SCRIPT, DEST_SCRIPT)


def files_equal(a, b):
    try:
        with open(a, "rb") as fa, open(b, "rb") as fb:
            return fa.read() == fb.read()
    except Exception:
        return False


def hook_group_has_command(group_list, substring):
    for group in group_list:
        for hook in group.get("hooks", []):
            if substring in hook.get("command", ""):
                return True
    return False


def ensure_hook(settings, event, command, status_message, timeout):
    groups = settings.setdefault("hooks", {}).setdefault(event, [])
    if hook_group_has_command(groups, "session_export.py"):
        return False
    groups.append(
        {
            "matcher": "*",
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "timeout": timeout,
                    "statusMessage": status_message,
                }
            ],
        }
    )
    return True


def main():
    install_script()

    if os.path.isfile(SETTINGS_PATH):
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            settings = json.load(f)
    else:
        settings = {}

    changed = False
    changed |= ensure_hook(
        settings,
        "SessionStart",
        BACKFILL_CMD,
        "이전 세션 백업 확인 중...",
        30,
    )
    changed |= ensure_hook(
        settings,
        "SessionEnd",
        SESSION_CMD,
        "세션 대화 저장 중...",
        15,
    )

    if changed:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
