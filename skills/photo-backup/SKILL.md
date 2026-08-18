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
