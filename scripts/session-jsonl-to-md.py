#!/usr/bin/env python3
"""Render Claude Code session transcripts (.jsonl) into one readable Markdown file.

Usage: session-jsonl-to-md.py OUT.md IN1.jsonl [IN2.jsonl ...]

Unlike export-session-to-obsidian.py (160-char snippets), this keeps the full
text of every user/assistant message and the full input of every tool call
(commands, written files, edits), so the work can be reproduced from the log.
Tool results are truncated. Subagent logs found next to each input
(<stem>/subagents/*.jsonl) are appended as their own sections.
"""
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
RESULT_LIMIT = 2500
INPUT_LIMIT = 40000


def ts_kst(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(KST)
    except Exception:
        return None


def fence(text, lang=""):
    text = str(text)
    if len(text) > INPUT_LIMIT:
        text = text[:INPUT_LIMIT] + f"\n... [{len(text) - INPUT_LIMIT} chars omitted]"
    tick = "````" if "```" in text else "```"
    return f"{tick}{lang}\n{text}\n{tick}"


def flatten(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                parts.append(flatten(c.get("text", c.get("content", ""))))
            else:
                parts.append(str(c))
        return "\n".join(p for p in parts if p)
    return str(content)


def render_tool_use(b):
    name = b.get("name", "?")
    inp = b.get("input", {}) or {}
    out = [f"**Tool: {name}**"]
    if name == "Bash":
        if inp.get("description"):
            out.append(f"_{inp['description']}_")
        out.append(fence(inp.get("command", ""), "bash"))
    elif name == "Write":
        out.append(f"Write `{inp.get('file_path', '')}`")
        out.append(fence(inp.get("content", "")))
    elif name == "Edit":
        out.append(f"Edit `{inp.get('file_path', '')}`")
        out.append("old:\n" + fence(inp.get("old_string", "")))
        out.append("new:\n" + fence(inp.get("new_string", "")))
    else:
        out.append(fence(json.dumps(inp, ensure_ascii=False, indent=1), "json"))
    return "\n".join(out)


def render_blocks(content):
    if isinstance(content, str):
        return [content.strip()] if content.strip() else []
    out = []
    for b in content or []:
        if not isinstance(b, dict):
            continue
        t = b.get("type")
        if t == "text" and b.get("text", "").strip():
            out.append(b["text"].strip())
        elif t == "tool_use":
            out.append(render_tool_use(b))
        elif t == "tool_result":
            s = flatten(b.get("content", ""))
            if len(s) > RESULT_LIMIT:
                s = s[:RESULT_LIMIT] + f"\n... [{len(s) - RESULT_LIMIT} chars omitted]"
            out.append("Result:\n" + fence(s))
        elif t == "image":
            out.append("_[image]_")
    return out


def render_session(src, title):
    session_id, cwd, sections, times = src.stem, "", [], []
    with src.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") not in ("user", "assistant") or "message" not in e:
                continue
            session_id = e.get("sessionId", session_id)
            cwd = cwd or e.get("cwd", "")
            ts = e.get("timestamp")
            t = ts_kst(ts) if ts else None
            if t:
                times.append(t)
            body = render_blocks(e["message"].get("content"))
            if not body:
                continue
            who = "User" if e["type"] == "user" else "Claude"
            stamp = t.strftime("%Y-%m-%d %H:%M:%S KST") if t else "(no timestamp)"
            sections.append(f"### {who} — {stamp}\n\n" + "\n\n".join(body))
    if not sections:
        return ""
    start, end = (min(times), max(times)) if times else (None, None)
    head = [f"## {title}", "", f"- source: `{src}`", f"- session id: `{session_id}`", f"- cwd: `{cwd}`"]
    if start:
        head.append(f"- span (KST): {start:%Y-%m-%d %H:%M} ~ {end:%Y-%m-%d %H:%M}")
    head.append(f"- messages: {len(sections)}")
    return "\n".join(head) + "\n\n" + "\n\n".join(sections) + "\n"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    out = Path(sys.argv[1])
    inputs = [Path(p) for p in sys.argv[2:]]
    parts = [
        f"# Claude Code 세션 로그 모음",
        "",
        f"- generated: {datetime.now(KST):%Y-%m-%d %H:%M KST}",
        f"- host: `{__import__('socket').gethostname()}`",
        "",
    ]
    for src in inputs:
        parts.append(render_session(src, f"Session {src.stem}"))
        for sub in sorted((src.parent / src.stem / "subagents").glob("*.jsonl")):
            parts.append(render_session(sub, f"Subagent {sub.stem} (of {src.stem[:8]})"))
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text("\n".join(p for p in parts if p), encoding="utf-8")
    shutil.move(str(tmp), str(out))
    print(out)


if __name__ == "__main__":
    main()
