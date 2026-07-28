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
