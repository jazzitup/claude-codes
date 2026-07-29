#!/bin/bash
# Pulls the latest hwpxskill upstream (Canine89/hwpxskill) into this repo's
# skills/hwpxskill submodule, and pushes the bump if anything changed.
# Scheduled daily by ~/Library/LaunchAgents/com.jazzitup.update-hwpxskill.plist.
set -euo pipefail

REPO_DIR="$HOME/claude-codes"
cd "$REPO_DIR"

git submodule update --remote --merge skills/hwpxskill

if ! git diff --quiet -- skills/hwpxskill; then
  git add skills/hwpxskill
  git commit -m "chore: update hwpxskill submodule"
  git push
  echo "$(date '+%Y-%m-%d %H:%M:%S') hwpxskill updated and pushed"
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') hwpxskill already up to date"
fi
