#!/bin/bash
# Mirrors the academic-search folder out of the claude-office-skills/skills
# monorepo (https://github.com/claude-office-skills/skills, ~150 unrelated
# skills — we only want this one) into skills/academic-search, and pushes
# the bump if anything changed.
# Scheduled daily by ~/Library/LaunchAgents/com.jazzitup.update-academic-search.plist.
set -euo pipefail

REPO_DIR="$HOME/claude-codes"
SRC_REPO="https://github.com/claude-office-skills/skills.git"
SKILL_PATH="academic-search"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

git clone --depth 1 --filter=blob:none --sparse "$SRC_REPO" "$TMP_DIR" >/dev/null 2>&1
git -C "$TMP_DIR" sparse-checkout set "$SKILL_PATH" >/dev/null 2>&1

rsync -a --delete "$TMP_DIR/$SKILL_PATH/" "$REPO_DIR/skills/$SKILL_PATH/"

cd "$REPO_DIR"
if ! git diff --quiet -- "skills/$SKILL_PATH"; then
  git add "skills/$SKILL_PATH"
  git commit -m "chore: sync academic-search skill from claude-office-skills/skills"
  git push
  echo "$(date '+%Y-%m-%d %H:%M:%S') academic-search updated and pushed"
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') academic-search already up to date"
fi
