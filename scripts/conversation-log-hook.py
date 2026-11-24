#!/usr/bin/env python3
"""Append-only conversation log for every Claude Code turn.

Runs on UserPromptSubmit (logs the prompt right away) and Stop (logs Claude's
reply, then appends any new transcript lines to a raw append-only copy).
Never rewrites or truncates what is already logged, so the log survives even
if Claude Code's own transcript (.jsonl) loses lines.

Logs live in Dropbox (private, never in a git repo — they can hold account
numbers and other personal data): <LOG_ROOT>/<host>/<session_id>.md and
<LOG_ROOT>/<host>/raw/<session_id>.jsonl
"""
import json
import os
import socket
import sys
from datetime import datetime

DROPBOX_ROOT = os.path.expanduser("~/Library/CloudStorage/Dropbox/claude-logs")
LOCAL_ROOT = os.path.expanduser("~/.claude/conversation-log")


def log_dir():
    root = DROPBOX_ROOT if os.path.isdir(os.path.dirname(DROPBOX_ROOT)) else LOCAL_ROOT
    d = os.path.join(root, socket.gethostname().split(".")[0])
    os.makedirs(os.path.join(d, "raw"), exist_ok=True)
    return d


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append(path, text):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def md_path(d, data):
    p = os.path.join(d, f"{data.get('session_id', 'unknown')}.md")
    if not os.path.exists(p):
        append(p, f"# Claude Code session {data.get('session_id')}\n\n"
                  f"- host: {socket.gethostname()}\n- cwd: {data.get('cwd', '')}\n"
                  f"- transcript: {data.get('transcript_path', '')}\n\n")
    return p


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def last_reply(transcript):
    """Assistant text blocks after the most recent real user prompt."""
    try:
        rows = [json.loads(l) for l in open(transcript, encoding="utf-8") if l.strip()]
    except (OSError, ValueError):
        return ""
    out = []
    for r in reversed(rows):
        msg = r.get("message") or {}
        if r.get("type") == "user" and isinstance(msg.get("content"), str):
            break
        if r.get("type") == "assistant":
            t = text_of(msg.get("content"))
            if t.strip():
                out.append(t)
    return "\n\n".join(reversed(out))


def backup_raw(d, data):
    """Append transcript lines not yet copied. If the transcript shrank,
    keep a full snapshot instead of losing anything."""
    src = data.get("transcript_path")
    if not src or not os.path.exists(src):
        return
    sid = data.get("session_id", "unknown")
    dst = os.path.join(d, "raw", f"{sid}.jsonl")
    state = os.path.join(d, "raw", f"{sid}.count")
    with open(src, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    done = int(open(state).read() or 0) if os.path.exists(state) else 0
    if len(lines) < done:
        snap = os.path.join(d, "raw", f"{sid}.shrunk-{datetime.now():%Y%m%d-%H%M%S}.jsonl")
        with open(snap, "w", encoding="utf-8") as f:
            f.writelines(lines)
        append(md_path(d, data), f"\n> [{now()}] WARNING: transcript shrank "
                                 f"({done} -> {len(lines)} lines); snapshot kept: {snap}\n")
        done = 0
        dst = os.path.join(d, "raw", f"{sid}.after-shrink.jsonl")
    if len(lines) > done:
        with open(dst, "a", encoding="utf-8") as f:
            f.writelines(lines[done:])
    with open(state, "w") as f:
        f.write(str(len(lines)))


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    d = log_dir()
    event = data.get("hook_event_name", "")
    if event == "UserPromptSubmit":
        append(md_path(d, data), f"\n## [{now()}] 사용자\n\n{data.get('prompt', '')}\n")
    elif event == "Stop":
        reply = data.get("last_assistant_message") or last_reply(data.get("transcript_path", ""))
        if reply:
            append(md_path(d, data), f"\n## [{now()}] Claude\n\n{reply}\n")
        backup_raw(d, data)


if __name__ == "__main__":
    main()
