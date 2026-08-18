---
name: photo-backup
description: Back up all photos and videos from Dropbox and Google Drive into a "visual memory" archive on an external drive, organized by year.month (e.g. 2025.09), with videos kept in a separate videos/ folder and represented by a Finder alias inside their year.month folder. Use when the user asks to back up / archive photos or videos from cloud storage to an external drive, or says "photo backup" / "사진 백업".
---

# Photo Backup

Incrementally copies every photo/video from Dropbox and Google Drive into a
dated archive on an external drive, called `visual memory`.

## Destination layout

```
<external drive>/visual memory/
  2025.09/                  # photos taken in Sep 2025
    IMG_1234.jpg
    some_video.mov          # <- Finder ALIAS, not the real file
  2025.10/
    ...
  videos/                   # the actual video files live here
    some_video.mov
  .photo_backup_manifest.tsv   # sha256 dedupe manifest (don't delete — enables incremental reruns)
```

- Year.month bucket is taken from the photo/video's EXIF/QuickTime "date taken"
  (DateTimeOriginal / CreateDate / MediaCreateDate), falling back to file
  creation/modification time if no metadata exists.
- Videos are physically stored under `videos/`; a Finder alias to the real
  file is placed in the matching `YYYY.MM/` folder so browsing by month still
  shows videos in place.
- Re-running the skill is safe and incremental: a sha256 manifest
  (`.photo_backup_manifest.tsv` at the root of `visual memory/`) tracks every
  file already backed up by content hash, so already-copied files (even if
  renamed or moved in the source) are skipped, not duplicated.
- Originals in Dropbox / Google Drive are never modified or deleted — this is
  a copy-only backup.

## How to run

Always process Dropbox first, then Google Drive (per user's stated order),
unless the user says otherwise.

```bash
python3 ~/.claude/skills/photo-backup/scripts/photo_backup.py \
  --source "$HOME/Library/CloudStorage/Dropbox" \
  --dest-base "/Volumes/<drive name>/visual memory"

python3 ~/.claude/skills/photo-backup/scripts/photo_backup.py \
  --source "$HOME/Library/CloudStorage/GoogleDrive-<account>" \
  --dest-base "/Volumes/<drive name>/visual memory"
```

Notes for whoever (human or Claude) invokes this:

- Confirm the external drive is mounted (`ls /Volumes`) and writable before
  running.
- Google Drive is normally in "Stream files" mode: reading a file to copy it
  forces an on-demand download, which is much slower than a local Dropbox
  copy and consumes bandwidth. Warn the user if the Google Drive pass looks
  like it will take a long time.
- This can process tens of thousands of files and take a long time — prefer
  running it with `run_in_background` and reporting the tail of progress
  lines (`progress: X/Y processed=... dupes=... errors=...`) rather than
  streaming all output inline.
- Requires `exiftool` (`brew install exiftool`) on PATH.
- If a file with the exact same content (by sha256) was already backed up
  under a different name/location, it is skipped and counted as a "dupe" —
  this is expected, not an error.
- `--exclude <path>` (repeatable) skips a whole subtree entirely — use it for
  a folder the user wants to handle separately (too large, needs manual
  attention, etc). Pass the path exactly as the user names it; the script
  NFC-normalizes both the exclude arg and the walked paths internally, so
  Korean/Unicode folder names match correctly even though macOS/Dropbox
  return filenames in NFD form.
- Per-file copies use a *stall*-based timeout (`copy_with_stall_detection`):
  a file only fails if its destination stops **growing** for
  `STALL_TIMEOUT_SECONDS` (120s) — a slow-but-progressing large download is
  never killed, only a genuinely stuck one. There's also an absolute
  `MAX_COPY_SECONDS` safety cap (2h). Failures (timeout or other errors) are
  appended to `.photo_backup_failed.tsv` (`source_path\treason`) at the root
  of `visual memory/` — check this file after a run for anything that needs
  manual follow-up.
- The exiftool metadata batch read is ALSO manually polled with a hard kill
  (`EXIFTOOL_TIMEOUT_SECONDS`, 120s) instead of relying on
  `subprocess.run(timeout=...)` — that flat timeout was empirically observed
  to sometimes not fire at all (a batch sat blocked in `select()` for 10+
  minutes past its 180s timeout with nothing in the log and no child process
  visible). Don't reintroduce a bare `subprocess.run(timeout=...)` for
  anything long-running in this script; always use a Popen + manual
  poll-and-kill loop instead.
- Every file the script touches is logged immediately and unbuffered:
  `CURRENT_BATCH: reading metadata for N files (i-j/total)` before each
  exiftool call, and `CURRENT_FILE: <path>` right before each copy attempt.
  This is what makes "what file is it on right now / is it actually stuck"
  answerable by just tailing the log — don't remove this logging even though
  it makes the log verbose.
- **Cloud "online-only" reversion is NOT automatable.** After copying a file
  that was a cloud placeholder, macOS/Dropbox provide no safe scriptable way
  to evict it back to online-only and free local disk space:
  - Finder's own contextual-menu "Make Online-Only" cannot be reliably
    triggered via AppleScript/System Events UI scripting on current macOS
    (Finder's rewrite broke `AXShowMenu`/control-click simulation for
    Finder-Sync-extension menu items), even with Accessibility permission
    granted.
  - The legacy `dropbox.py` / `~/.dropbox/command_socket` CLI does not work
    with the modern File-Provider-based Dropbox client ("Dropbox isn't
    running!" even while it is).
  - The real public API for this, `NSFileProviderManager.evictItem`, refuses
    to run ("The application cannot be used right now") from a script or an
    ad-hoc-signed helper app — it requires a properly Apple-Developer-signed
    app.
  - **Conclusion**: if local disk space is a concern, either (a) let the
    watchdog below guard against filling the disk and revert to online-only
    manually via Finder afterward, or (b) `--exclude` any single folder too
    large to safely materialize all at once and have the user back it up
    separately by hand.
- Pair every run with a disk-space watchdog on the internal drive (kill the
  backup process if free space drops below a safety floor, e.g. 15GB) since
  cloud placeholder files get materialized locally as they're read and nothing
  automatically evicts them afterward.
