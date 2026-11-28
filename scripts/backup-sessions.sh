#!/bin/bash
# SessionEnd hook: back up every Claude Code transcript on this Mac
# (~/.claude/projects/**/*.jsonl) into the private repo jazzitup/claude-sessions.
# Several Macs push to the same repo, so pull --rebase before pushing.
set -uo pipefail
SRC="$HOME/.claude/projects"
REPO="$HOME/claude-sessions"
LOG=/tmp/claude-sessions-backup.log
[ -d "$REPO/.git" ] || exit 0
mkdir -p "$REPO/sessions"
rsync -a --include='*/' --include='*.jsonl' --exclude='*' "$SRC/" "$REPO/sessions/"
cd "$REPO" || exit 0
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "Session backup $(hostname -s) $(date '+%Y-%m-%d %H:%M:%S')" --quiet
fi
git pull --rebase --quiet origin main >>"$LOG" 2>&1 || git rebase --abort >/dev/null 2>&1
git push --quiet origin HEAD >>"$LOG" 2>&1 || true
