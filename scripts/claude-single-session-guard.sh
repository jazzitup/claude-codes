#!/bin/bash
# Exit 1 (with a message) if a Claude Code process on THIS computer is already running
# in the given directory (default: current directory). Paths are compared after
# resolving symlinks, so ~/claude_workspace/<link> and its real Dropbox/Drive path match.
# Other computers are not checked — their sessions keep separate transcripts.
# Used by the run*.sh launchers: guard || exit 1
here=$(cd "${1:-.}" && pwd -P) || exit 0
for pid in $(ps -axo pid=,comm= | awk '$2 == "claude" {print $1}'); do
  [ "$pid" = "$PPID" ] && continue
  dir=$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')
  [ -n "$dir" ] && dir=$(cd "$dir" 2>/dev/null && pwd -P)
  if [ "$dir" = "$here" ]; then
    echo "이 디렉토리에서 Claude 세션이 이미 실행 중입니다 (PID $pid). 그 창을 쓰세요." >&2
    echo "정말 하나 더 열려면 run 스크립트 없이 claude 를 직접 실행하세요." >&2
    exit 1
  fi
done
exit 0
