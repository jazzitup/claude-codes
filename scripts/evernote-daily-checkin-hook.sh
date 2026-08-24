#!/bin/bash
# SessionStart hook: remind Claude to run the evernote-daily-checkin skill.
# Static message only -- all real logic (finding today's note/row, interviewing
# the user, writing back to Evernote) lives in the skill itself, which is kept
# in sync across computers via this same claude-codes git repo.
cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"세션 시작 체크: evernote-daily-checkin 스킬을 참고해서, Evernote MCP가 이 세션에 연결되어 있으면 이번 주 Evernote 노트의 'Morning Routine' 표에서 오늘 날짜 칸의 세 항목(전날 밤 공복 유지 O/X, 아침 공부 시간 시:분, 밤 조깅 O/X)이 채워져 있는지 확인하라. 비어있는 항목이 하나라도 있으면 사용자에게 인터뷰 형식으로 그 항목들만 물어보고, 답을 받으면 즉시 그 노트 셀에 채워 넣어라. 오늘 항목이 이미 다 채워져 있거나 Evernote MCP가 연결되어 있지 않으면 조용히 넘어가고 언급하지 않는다. 세션당 한 번만 확인한다."}}
EOF
