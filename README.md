# claude-codes

Personal [Claude Code](https://claude.com/claude-code) skills, plugins, and
configs — kept here so they can be pulled onto any machine instead of living
only in `~/.claude/` on one laptop.

## Layout

```
skills/<skill-name>/     one Claude Code skill per directory,
                          same shape as ~/.claude/skills/<skill-name>/
```

## Install a skill on a new machine

```bash
git clone git@github.com:jazzitup/claude-codes.git
cp -R claude-codes/skills/<skill-name> ~/.claude/skills/<skill-name>
```

(or symlink the whole `skills/` directory in as `~/.claude/skills` if you
want it to stay in sync with `git pull`).

## Skills

- **[pennylane-codebook-notes](skills/pennylane-codebook-notes/)** —
  generates a detailed Korean lecture note (Google-Docs-paste-ready HTML,
  with real rendered formula/diagram images) from PennyLane Codebook Theory
  tabs. See its `SKILL.md` for the pipeline and prerequisites (TeX Live,
  `librsvg`).
- **[lecture-history-enrich](skills/lecture-history-enrich/)** — takes an
  existing lecture-note HTML (e.g. one made by `pennylane-codebook-notes`)
  and adds short "science history" episode boxes + portrait photos of the
  people behind each concept, sourced from Wikipedia/Wikimedia Commons and
  embedded as base64 images matching the note's existing design system.
  Always writes a new file, never overwrites the original.
- **[hwpxskill](skills/hwpxskill/)** — git submodule tracking
  [Canine89/hwpxskill](https://github.com/Canine89/hwpxskill). Generates,
  reads, and edits Hancom `.hwpx` (OWPML) documents by working with the XML
  directly. Refuses `.hwp` binary output. Auto-updated every morning by
  `scripts/update-hwpxskill.sh` (see below); to update by hand run
  `git submodule update --remote --merge skills/hwpxskill`.
- **[academic-search](skills/academic-search/)** — plain mirror (not a
  submodule — source is one folder inside a ~150-skill monorepo) of
  `academic-search/` from
  [claude-office-skills/skills](https://github.com/claude-office-skills/skills).
  Searches/analyzes academic literature: finding papers, assessing
  methodology, synthesizing findings. Auto-synced every morning by
  `scripts/update-academic-search.sh`; to update by hand just re-run that
  script.
- **[indico-stats](skills/indico-stats/)** — pulls registration and
  abstract-submission stats from an Indico event's admin/manager pages
  (country, affiliation, position type, track, Theory/Experiment category —
  fields only visible after logging in, not on the public event page) and
  renders an HTML dashboard via `scripts/build_report.py` (stdlib only, no
  deps). `SKILL.md` documents the browser-automation collection steps and
  the JSON schema the script consumes; `examples/quark_matter_2027.json` is
  a real worked example.
- **[evernote-weekly-todo](skills/evernote-weekly-todo/)** — creates the next
  week's note in a recurring Evernote "weekly todo" series (titled like
  `June 4`, `July 3`, `August 2`) by copying the table structure from a
  dedicated template note (`attributes.isTemplate: true`) and filling in
  that week's Sun–Sat dates. No personal note content, links, or GUIDs are
  hardcoded in `SKILL.md` — everything is read live from the user's own
  Evernote via `get_note` each time.

## Auto-updating third-party skills

`scripts/update-hwpxskill.sh` and `scripts/update-academic-search.sh` each
pull the latest upstream version of their skill and, if anything changed,
commit + push that bump. Both are scheduled daily via macOS LaunchAgents
(`~/Library/LaunchAgents/com.jazzitup.update-hwpxskill.plist` at 8:00am,
`com.jazzitup.update-academic-search.plist` at 8:05am); logs go to
`scripts/update-*.log`. Claude Code re-reads skill files at the start of
every session, so no separate "reload" step is needed beyond starting a new
session after the pull.

## Mac shortcuts (auto-installed)

`mac-shortcuts/install.sh` installs macOS keyboard shortcuts as Automator
Quick Actions (`~/Library/Services`) bound via `pbs NSServicesStatus`. It is
idempotent and runs at every Claude Code session start through
`scripts/session-start-setup.sh` (called from the evernote check-in hook), so
any Mac that pulls this repo gets them automatically.

- **Control+Option+Command+S** — `qft_layout.sh`: opens the Schwartz QFT PDF and its
  copy in Preview; original fills the leftmost monitor, copy takes the left
  half of the rightmost monitor (single screen: only the original, filling the screen).
- **iTerm2 Ctrl+A / Ctrl+E with Korean input**: `iterm2_korean_ctrl.sh` adds
  physical-key `GlobalKeyMap` bindings so Ctrl+A/E still send `0x01`/`0x05`
  when the input source is Korean, and sets `LanguageAgnosticKeyBindings`. It also
  runs from `session-start-setup.sh`. It takes effect after restarting iTerm2 (⌘Q).

## Time-activated pending tasks (`pending-tasks/`)

Drop a markdown file in `pending-tasks/` with a header

```
---
from_epoch: <utc epoch>
until_epoch: <utc epoch>
---
```

and `scripts/pending-tasks-hook.sh` (called from the SessionStart hook
`scripts/evernote-daily-checkin-hook.sh`) injects its body into every new
Claude Code session that starts inside that window — on any machine that has
pulled this repo and registered that SessionStart hook. When done, move the
file to `pending-tasks/done/` and push so other machines stop seeing it.
