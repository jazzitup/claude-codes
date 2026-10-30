#!/bin/bash
# SessionStart hook: remind Claude to run the evernote-daily-checkin skill,
# and inject any time-activated pending task from pending-tasks/ (see
# scripts/pending-tasks-hook.sh). Static message only for Evernote -- all real
# logic lives in the skill itself, kept in sync across computers via this repo.
# Also install local Mac shortcuts from this repo (idempotent; see mac-shortcuts/).
"$HOME/claude-codes/scripts/session-start-setup.sh" &
EVERNOTE="세션 시작 체크: evernote-daily-checkin 스킬을 참고해서, Evernote MCP가 이 세션에 연결되어 있으면 이번 주 Evernote weekly-todo 노트의 'Routine' 표에서 오늘 칸의 '전날 밤 공복 유지'(O/X)·'아침'(자유 텍스트)·'요코하마 선언'(O/X)을 확인한다. 비어있는 항목이 하나라도 있으면 사용자에게 인터뷰 형식으로 그 항목들만 물어보고, 답을 받으면 즉시 그 노트 셀에 채워 넣어라. 확인 대상이 이미 다 채워져 있거나 Evernote MCP가 연결되어 있지 않으면 조용히 넘어가고 언급하지 않는다. 세션당 한 번만 확인한다."
PENDING=$("$HOME/claude-codes/scripts/pending-tasks-hook.sh" 2>/dev/null)
if [ -n "$PENDING" ]; then
  CTX="$EVERNOTE

아래는 시간이 되어 활성화된 대기 작업이다. Evernote 체크인보다 먼저, 세션 시작 즉시 수행한다.
$PENDING"
else
  CTX="$EVERNOTE"
fi
# python3 (ships with macOS CLT) instead of jq, which may be missing on another Mac
CTX="$CTX" python3 -c 'import json,os;print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":os.environ["CTX"]}},ensure_ascii=False))'
