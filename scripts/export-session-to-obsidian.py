#!/usr/bin/env python3
"""Export one Claude Code session transcript (.jsonl) to a Markdown log in the
Obsidian vault (My Drive/Obsidian/claude_note/), in the same format as the
existing "Claude 세션 ... (id8).md" notes there.

Usage: export-session-to-obsidian.py <transcript.jsonl> [out_dir]
Re-running for the same session replaces its previous export (matched by the
"(<first 8 chars of session id>).md" suffix), so resumed sessions stay one file.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_OUT = Path.home() / "Library/CloudStorage/GoogleDrive-kingmking@gmail.com/My Drive/Obsidian/claude_note"
SNIP = 160


def snippet(s):
    s = " ".join(str(s).split()).replace("`", "'")
    return s if len(s) <= SNIP else s[:SNIP] + "..."


def parse_ts(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def flatten(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(flatten(c.get("text", c.get("content", ""))) if isinstance(c, dict) else str(c) for c in content)
    return str(content)


def render_blocks(role, content):
    """Return markdown lines for one message's content."""
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
            out.append(f"> 🔧 **{b.get('name', '?')}**: `{snippet(json.dumps(b.get('input', {}), ensure_ascii=False))}`")
        elif t == "tool_result":
            out.append(f"> ↳ 결과: `{snippet(flatten(b.get('content', '')))}`")
    return out


def main():
    src = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    if not src.is_file() or not out_dir.is_dir():
        return
    session_id, cwd, sections, times = src.stem, "", [], []
    with src.open(encoding="utf-8") as f:
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
            if not ts:
                continue
            times.append(parse_ts(ts))
            body = render_blocks(e["type"], e["message"].get("content"))
            if body:
                who = "🧑 User" if e["type"] == "user" else "🤖 Claude"
                sections.append(f"### {who} ({ts})\n\n" + "\n\n".join(body))
    if not sections:
        return
    start, end = min(times), max(times)
    if start.date() == end.date():
        span = f"{start:%Y-%m-%d %H%M}-{end:%H%M}"
    else:
        span = f"{start:%Y-%m-%d %H%M} to {end:%Y-%m-%d %H%M}"
    id8 = session_id[:8]
    name = f"Claude 세션 {span} ({id8}).md"
    header = (
        "---\ntags:\n  - claude-code\n  - session-log\n"
        f"session_id: {session_id}\ncwd: {cwd}\nstart: {start.isoformat()}\nend: {end.isoformat()}\n---\n\n"
        "# Claude Code 세션 로그\n\n"
        f"**기간**: {start.isoformat(' ')} ~ {end.isoformat(' ')}\n"
        f"**작업 디렉토리**: `{cwd}`\n"
        f"**세션 ID**: `{session_id}`\n\n## 대화\n\n"
    )
    tmp = out_dir / f".{name}.tmp"
    tmp.write_text(header + "\n\n".join(sections) + "\n", encoding="utf-8")
    for old in out_dir.glob(f"Claude 세션 * ({id8}).md"):
        old.unlink()
    os.replace(tmp, out_dir / name)
    print(out_dir / name)


if __name__ == "__main__":
    main()
