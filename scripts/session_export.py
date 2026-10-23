#!/usr/bin/env python3
import json
import sys
import glob
import os
import re
from datetime import datetime

OBSIDIAN_DIR = os.environ.get(
    "CLAUDE_SESSION_EXPORT_DIR",
    os.path.expanduser("/Users/yongsunkim/My GDrive/Obsidian/claude_note"),
)
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")


def read_stdin_json():
    try:
        data = sys.stdin.read()
        return json.loads(data) if data.strip() else {}
    except Exception:
        return {}


def find_transcript_path(hook_input):
    tp = hook_input.get("transcript_path")
    if tp and os.path.isfile(tp):
        return tp
    session_id = hook_input.get("session_id")
    cwd = hook_input.get("cwd")
    if session_id and cwd:
        sanitized = cwd.replace("/", "-")
        candidate = os.path.join(PROJECTS_DIR, sanitized, f"{session_id}.jsonl")
        if os.path.isfile(candidate):
            return candidate
    if session_id:
        matches = glob.glob(os.path.join(PROJECTS_DIR, "*", f"{session_id}.jsonl"))
        if matches:
            return matches[0]
    return None


def extract_text_blocks(content):
    parts = []
    if isinstance(content, str):
        if content.strip():
            parts.append(content.strip())
    elif isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                t = block.get("text", "").strip()
                if t:
                    parts.append(t)
            elif btype == "tool_use":
                name = block.get("name", "tool")
                inp = block.get("input", {})
                summary = json.dumps(inp, ensure_ascii=False)
                if len(summary) > 160:
                    summary = summary[:160] + "..."
                parts.append(f"> 🔧 **{name}**: `{summary}`")
            elif btype == "tool_result":
                c = block.get("content")
                if isinstance(c, list):
                    c = " ".join(
                        b.get("text", "") for b in c if isinstance(b, dict)
                    )
                c = (c or "").strip().replace("\n", " ")
                if len(c) > 160:
                    c = c[:160] + "..."
                if c:
                    parts.append(f"> ↳ 결과: `{c}`")
    return parts


def parse_transcript(path):
    messages = []
    start_ts = None
    end_ts = None
    cwd = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts = d.get("timestamp")
            if ts:
                if start_ts is None:
                    start_ts = ts
                end_ts = ts
            if not cwd and d.get("cwd"):
                cwd = d.get("cwd")
            t = d.get("type")
            if t not in ("user", "assistant"):
                continue
            msg = d.get("message", {})
            content = msg.get("content")
            parts = extract_text_blocks(content)
            if parts:
                messages.append((t, ts, parts))
    return messages, start_ts, end_ts, cwd


def fmt_ts(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def build_markdown(session_id, messages, start_ts, end_ts, cwd):
    start_dt = fmt_ts(start_ts)
    end_dt = fmt_ts(end_ts)
    lines = []
    lines.append("---")
    lines.append("tags:")
    lines.append("  - claude-code")
    lines.append("  - session-log")
    lines.append(f"session_id: {session_id}")
    if cwd:
        lines.append(f"cwd: {cwd}")
    if start_dt:
        lines.append(f"start: {start_dt.isoformat()}")
    if end_dt:
        lines.append(f"end: {end_dt.isoformat()}")
    lines.append("---")
    lines.append("")
    lines.append("# Claude Code 세션 로그")
    lines.append("")
    if start_dt and end_dt:
        lines.append(f"**기간**: {start_dt} ~ {end_dt}")
    if cwd:
        lines.append(f"**작업 디렉토리**: `{cwd}`")
    lines.append(f"**세션 ID**: `{session_id}`")
    lines.append("")
    lines.append("## 대화")
    lines.append("")
    for role, ts, parts in messages:
        label = "🧑 User" if role == "user" else "🤖 Claude"
        lines.append(f"### {label} ({ts or ''})")
        lines.append("")
        for p in parts:
            lines.append(p)
            lines.append("")
    return "\n".join(lines)


def make_filename(session_id, start_ts, end_ts):
    start_dt = fmt_ts(start_ts)
    end_dt = fmt_ts(end_ts)
    short_id = session_id[:8] if session_id else "unknown"
    if start_dt and end_dt:
        if start_dt.date() == end_dt.date():
            span = f"{start_dt:%Y-%m-%d} {start_dt:%H%M}-{end_dt:%H%M}"
        else:
            span = f"{start_dt:%Y-%m-%d %H%M} to {end_dt:%Y-%m-%d %H%M}"
    else:
        span = "unknown-time"
    return f"Claude 세션 {span} ({short_id}).md"


def already_exported(session_id):
    if not os.path.isdir(OBSIDIAN_DIR):
        return False
    pattern = re.compile(re.escape(session_id))
    for fname in os.listdir(OBSIDIAN_DIR):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(OBSIDIAN_DIR, fname)
        try:
            with open(fpath, encoding="utf-8") as f:
                head = f.read(1000)
            if pattern.search(head):
                return True
        except Exception:
            continue
    return False


def export_one(path, session_id=None):
    if session_id is None:
        session_id = os.path.splitext(os.path.basename(path))[0]
    if already_exported(session_id):
        return None
    messages, start_ts, end_ts, cwd = parse_transcript(path)
    if not messages:
        return None
    md = build_markdown(session_id, messages, start_ts, end_ts, cwd)
    os.makedirs(OBSIDIAN_DIR, exist_ok=True)
    fname = make_filename(session_id, start_ts, end_ts)
    fpath = os.path.join(OBSIDIAN_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(md)
    return fpath


def cmd_session():
    hook_input = read_stdin_json()
    session_id = hook_input.get("session_id")
    path = find_transcript_path(hook_input)
    if not path:
        print(json.dumps({"systemMessage": "session_export: transcript not found, skipped"}))
        return
    result = export_one(path, session_id)
    if result:
        print(json.dumps({"systemMessage": f"세션 로그 저장됨: {os.path.basename(result)}"}))
    else:
        print(json.dumps({"suppressOutput": True}))


def cmd_backfill():
    hook_input = read_stdin_json()
    current_session_id = hook_input.get("session_id")
    exported = []
    for path in glob.glob(os.path.join(PROJECTS_DIR, "*", "*.jsonl")):
        session_id = os.path.splitext(os.path.basename(path))[0]
        if session_id == current_session_id:
            continue
        result = export_one(path, session_id)
        if result:
            exported.append(os.path.basename(result))
    if exported:
        print(json.dumps({"systemMessage": f"이전 세션 {len(exported)}건 백업 저장됨"}))
    else:
        print(json.dumps({"suppressOutput": True}))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "session"
    if mode == "backfill":
        cmd_backfill()
    else:
        cmd_session()
