---
name: receipt-scan
description: Convert a receipt photo (HEIC/JPG/etc) into a PNG named "<금액>원_<YYYY.MM.DD>.png" by reading the total payment amount and date off the receipt image. Use when the user gives one or more receipt image file paths and asks to process/rename/organize them as receipts, or says "영수증 스캔 처리" / "영수증 파일 정리".
---

# Receipt Scan Processing

Turns a raw receipt photo into a self-describing filename so receipts are
identifiable at a glance in Finder without opening each one.

## For each receipt file

1. Convert to PNG for viewing (source can stay any format — HEIC is typical
   from iPhone):
   ```bash
   sips -s format png "<source>" --out "<scratch>/preview.png"
   ```
2. Read the PNG image (visually) and extract:
   - **총 결제금액** (the final total actually paid — look for 합계/결제금액/승인금액,
     not the pre-tax 공급가액 or the 부가세 line alone). If the receipt shows
     several totals (e.g. a running total per line plus a final one), use the
     last/bottom-most total, which is what was actually charged.
   - **거래 날짜** on the receipt (not today's date, not the file's mtime).
2b. If the amount or date is unreadable/ambiguous (blurry, cut off,
   handwritten, multiple candidate totals), stop and ask the user rather than
   guessing — a wrong amount in the filename is worse than no filename.
3. Build the destination filename: `<금액>원_<YYYY.MM.DD>.png` — amount as a
   plain integer with no thousands separator (e.g. `15800원`, not
   `15,800원`), date zero-padded with dots (e.g. `2026.07.30`). Match this
   exact format even if the user's phrasing varies slightly — confirm the
   format with the user if they give a different example than this.
4. Convert the original directly to that final path:
   ```bash
   sips -s format png "<source>" --out "<same-dir>/<금액>원_<YYYY.MM.DD>.png"
   ```
5. Delete the original source file after the PNG is confirmed written —
   this is a rename+convert, not a copy, unless the user says otherwise.
6. If the target filename already exists (e.g. two receipts same amount same
   day), append `-2`, `-3`, ... before `.png` rather than overwriting.

## Batch processing

When given multiple receipt paths at once, process them one at a time in the
order given, each through the full steps above (view → confirm amount/date →
convert → delete original). Report a short summary table at the end (old
name → new name) rather than a running commentary per file.
