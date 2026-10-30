#!/bin/bash
# SessionStart helper: print (to stdout, plain text) every pending task in
# ~/claude-codes/pending-tasks/*.md whose activation window contains "now".
# A task file starts with a YAML-ish header holding from_epoch / until_epoch
# (UTC epoch seconds). Files in pending-tasks/done/ are ignored.
# Output is empty when nothing is active; evernote-daily-checkin-hook.sh merges
# it into its additionalContext so no extra hook registration is needed.
DIR="$HOME/claude-codes/pending-tasks"
[ -d "$DIR" ] || exit 0
now=$(date +%s)
for f in "$DIR"/*.md; do
  [ -f "$f" ] || continue
  from=$(sed -n 's/^from_epoch: *//p' "$f" | head -1)
  until=$(sed -n 's/^until_epoch: *//p' "$f" | head -1)
  [ -n "$from" ] && [ "$now" -lt "$from" ] && continue
  [ -n "$until" ] && [ "$now" -gt "$until" ] && continue
  printf '\n===== 대기 작업 (지금 실행할 것): %s =====\n' "$(basename "$f")"
  cat "$f"
  printf '\n===== 끝 =====\n'
done
exit 0
