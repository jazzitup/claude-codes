#!/usr/bin/env python3
"""Incremental photo/video backup: source cloud folder -> visual memory archive.

Layout on destination:
  <dest-base>/YYYY.MM/<photo files>          (photos, bucketed by date taken)
  <dest-base>/YYYY.MM/<video alias files>    (Finder aliases pointing into videos/)
  <dest-base>/videos/<video files>           (actual video files)
  <dest-base>/.photo_backup_manifest.tsv     (sha256 dedupe manifest, incremental)
"""
import argparse
import csv
import datetime
import hashlib
import json
import unicodedata
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

STALL_TIMEOUT_SECONDS = 120   # abort if dest file stops growing for this long
MAX_COPY_SECONDS = 2 * 3600   # absolute safety cap per file, even if still slowly growing
POLL_INTERVAL_SECONDS = 5


class FileTimeout(Exception):
    pass

PHOTO_EXT = {"jpg", "jpeg", "png", "heic", "heif", "tiff", "tif", "gif", "bmp",
             "raw", "cr2", "cr3", "nef", "arw", "dng", "webp"}
VIDEO_EXT = {"mp4", "mov", "m4v", "avi", "mkv", "wmv", "3gp", "mts", "m2ts"}

DATE_TAGS = ["DateTimeOriginal", "CreateDate", "MediaCreateDate", "TrackCreateDate", "FileModifyDate"]


def run_exiftool_batch(paths):
    if not paths:
        return {}
    with tempfile.NamedTemporaryFile("w", suffix=".args", delete=False) as f:
        for p in paths:
            f.write(p + "\n")
        argfile = f.name
    cmd = ["exiftool", "-j", "-q", "-m"] + [f"-{t}" for t in DATE_TAGS] + ["-@", argfile]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        data = json.loads(out.stdout) if out.stdout.strip() else []
    except Exception as e:
        print(f"exiftool batch failed: {e}", file=sys.stderr, flush=True)
        data = []
    finally:
        os.unlink(argfile)
    return {m.get("SourceFile"): m for m in data}


def parse_exif_date(s):
    if not s:
        return None
    m = re.match(r"(\d{4}):(\d{2}):(\d{2})", s)
    if m:
        y, mo, _ = m.groups()
        if y == "0000" or mo == "00":
            return None
        return int(y), int(mo)
    return None


def get_date_bucket(meta, filepath):
    for tag in DATE_TAGS:
        v = meta.get(tag) if meta else None
        r = parse_exif_date(v) if v else None
        if r:
            return r
    st = os.stat(filepath)
    dt = datetime.datetime.fromtimestamp(getattr(st, "st_birthtime", st.st_mtime))
    return dt.year, dt.month


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def copy_with_stall_detection(src, dst):
    """Copy via `cp` in a subprocess; abort only if dst stops GROWING for
    STALL_TIMEOUT_SECONDS (a genuinely stalled cloud download), not just if
    it's slow. Large-but-progressing downloads are allowed up to
    MAX_COPY_SECONDS as an absolute safety cap. Returns sha256 of dst."""
    proc = subprocess.Popen(["cp", src, str(dst)])
    last_size = -1
    last_growth = time.time()
    start = time.time()
    try:
        while True:
            ret = proc.poll()
            if ret is not None:
                if ret != 0:
                    raise RuntimeError(f"cp exited with code {ret}")
                break
            time.sleep(POLL_INTERVAL_SECONDS)
            try:
                cur_size = dst.stat().st_size
            except FileNotFoundError:
                cur_size = 0
            now = time.time()
            if cur_size > last_size:
                last_size = cur_size
                last_growth = now
            elif now - last_growth > STALL_TIMEOUT_SECONDS:
                proc.kill()
                proc.wait()
                raise FileTimeout(f"stalled: no growth for {STALL_TIMEOUT_SECONDS}s at {cur_size} bytes")
            if now - start > MAX_COPY_SECONDS:
                proc.kill()
                proc.wait()
                raise FileTimeout(f"exceeded max {MAX_COPY_SECONDS}s (size={cur_size})")
    except BaseException:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise
    return sha256_file(dst)


def unique_dest(dest_dir, filename):
    dest_dir.mkdir(parents=True, exist_ok=True)
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem, ext = os.path.splitext(filename)
    i = 1
    while True:
        candidate = dest_dir / f"{stem}__{i}{ext}"
        if not candidate.exists():
            return candidate
        i += 1


def load_manifest(manifest_path):
    seen = {}
    if manifest_path.exists():
        with open(manifest_path, newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                seen[row["sha256"]] = row["dest_path"]
    return seen


def append_manifest(manifest_path, row):
    exists = manifest_path.exists()
    with open(manifest_path, "a", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        if not exists:
            w.writerow(["source_path", "sha256", "dest_path", "kind", "year_month"])
        w.writerow(row)


def _applescript_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def make_alias(target_path, alias_dir, desired_name):
    alias_dir.mkdir(parents=True, exist_ok=True)
    t = _applescript_escape(target_path)
    d = _applescript_escape(str(alias_dir))
    script = f'''
    set targetItem to (POSIX file "{t}") as alias
    set destFolder to (POSIX file "{d}") as alias
    tell application "Finder"
        set newAlias to make new alias file at destFolder to targetItem
        return POSIX path of (newAlias as alias)
    end tell
    '''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    created = r.stdout.strip()
    if created and os.path.exists(created):
        target_name = alias_dir / desired_name
        if not target_name.exists() and created != str(target_name):
            os.rename(created, target_name)
    elif r.returncode != 0:
        print(f"alias creation failed for {target_path}: {r.stderr.strip()}", file=sys.stderr, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="Source folder to scan (Dropbox / Google Drive root)")
    ap.add_argument("--dest-base", required=True, help='Destination "visual memory" folder on external drive')
    ap.add_argument("--batch-size", type=int, default=150)
    ap.add_argument("--exclude", action="append", default=[],
                     help="Absolute path to skip entirely (repeatable). Anything under it is not scanned.")
    args = ap.parse_args()

    source = Path(args.source)
    dest_base = Path(args.dest_base)
    videos_dir = dest_base / "videos"
    manifest_path = dest_base / ".photo_backup_manifest.tsv"
    def norm(p):
        return unicodedata.normalize("NFC", os.path.normpath(p))

    excludes = [norm(e) for e in args.exclude]

    dest_base.mkdir(parents=True, exist_ok=True)
    seen = load_manifest(manifest_path)
    print(f"Loaded manifest: {len(seen)} files already backed up", flush=True)
    if excludes:
        print(f"Excluding: {excludes}", flush=True)

    all_files = []
    for root, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and norm(os.path.join(root, d)) not in excludes]
        if any(norm(root) == e or norm(root).startswith(e + os.sep) for e in excludes):
            continue
        for fn in files:
            if fn.startswith("."):
                continue
            ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
            if ext in PHOTO_EXT or ext in VIDEO_EXT:
                all_files.append(os.path.join(root, fn))

    total = len(all_files)
    print(f"Found {total} candidate photo/video files under {source}", flush=True)

    processed = 0
    skipped_dupe = 0
    errors = 0
    failed_path = dest_base / ".photo_backup_failed.tsv"

    for i in range(0, total, args.batch_size):
        batch = all_files[i:i + args.batch_size]
        print(f"CURRENT_BATCH: reading metadata for {len(batch)} files "
              f"({i+1}-{i+len(batch)}/{total})", flush=True)
        meta_by_file = run_exiftool_batch(batch)
        for fp in batch:
            dest = None
            try:
                print(f"CURRENT_FILE: {fp}", flush=True)
                meta = meta_by_file.get(fp, {})
                ext = fp.rsplit(".", 1)[-1].lower()
                kind = "photo" if ext in PHOTO_EXT else "video"
                year, month = get_date_bucket(meta, fp)
                ym = f"{year}.{month:02d}"
                month_dir = dest_base / ym

                if kind == "photo":
                    dest = unique_dest(month_dir, os.path.basename(fp))
                else:
                    dest = unique_dest(videos_dir, os.path.basename(fp))

                digest = copy_with_stall_detection(fp, dest)

                if digest in seen:
                    os.remove(dest)
                    skipped_dupe += 1
                    continue

                seen[digest] = str(dest)
                append_manifest(manifest_path, [fp, digest, str(dest), kind, ym])

                if kind == "video":
                    make_alias(str(dest), month_dir, dest.name)

                processed += 1
            except FileTimeout as e:
                errors += 1
                if dest is not None and dest.exists():
                    os.remove(dest)
                print(f"TIMEOUT on {fp}: {e}", file=sys.stderr, flush=True)
                with open(failed_path, "a") as f:
                    f.write(f"{fp}\ttimeout: {e}\n")
            except Exception as e:
                errors += 1
                if dest is not None and dest.exists():
                    try:
                        os.remove(dest)
                    except OSError:
                        pass
                print(f"ERROR on {fp}: {e}", file=sys.stderr, flush=True)
                with open(failed_path, "a") as f:
                    f.write(f"{fp}\t{e}\n")
        print(f"progress: {min(i + args.batch_size, total)}/{total} "
              f"processed={processed} dupes={skipped_dupe} errors={errors}", flush=True)

    print(f"DONE source={source} processed={processed} dupes={skipped_dupe} errors={errors}", flush=True)


if __name__ == "__main__":
    main()
