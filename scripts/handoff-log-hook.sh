#!/bin/bash
# SessionStart (startup/resume/clear/compact): if the session's directory keeps a shared
# handoff log (claude notes/SESSION_LOG.md, see the shared-dir-handoff-log skill), inject
# its latest entries so Claude starts every session — new or resumed — with the handoff.
input=$(cat)
cwd=$(printf '%s' "$input" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("cwd",""))' 2>/dev/null)
[ -n "$cwd" ] || cwd=$PWD
log="$cwd/claude notes/SESSION_LOG.md"
[ -f "$log" ] || exit 0
python3 - "$log" <<'EOF'
import json, sys
text = open(sys.argv[1], encoding="utf-8").read()
tail = text[-12000:]
msg = ("이 디렉토리는 여러 컴퓨터가 공유한다. 아래는 인수인계 로그(claude notes/SESSION_LOG.md)의 "
       "최근 부분이다. CLAUDE.md 규칙대로 이걸 기준으로 진행 상황을 파악하고, 첫 답변 맨 앞에 "
       "한두 줄로 인수인계 요약을 알린 뒤 시작하라.\n\n" + tail)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}},
                 ensure_ascii=False))
EOF
