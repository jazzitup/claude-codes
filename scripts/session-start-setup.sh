#!/bin/bash
# SessionStart: 이 Mac에 claude-codes 의 로컬 설정(단축키, 세션 자동 백업 등)을 설치한다. 이미 설치돼 있으면 즉시 종료.
"$HOME/claude-codes/mac-shortcuts/install.sh" >/dev/null 2>&1
python3 "$HOME/claude-codes/scripts/install_session_export.py" >/dev/null 2>&1
exit 0
