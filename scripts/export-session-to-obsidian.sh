#!/bin/bash
# SessionEnd hook: export the finished session to Obsidian (My Drive/Obsidian/claude_note/)
# as "Claude 세션 <start>-<end> (<id8>).md". Reads the hook JSON on stdin.
transcript=$(jq -r '.transcript_path // empty')
[ -n "$transcript" ] && [ -f "$transcript" ] || exit 0
python3 "$HOME/claude-codes/scripts/export-session-to-obsidian.py" "$transcript" >/dev/null 2>&1
exit 0
