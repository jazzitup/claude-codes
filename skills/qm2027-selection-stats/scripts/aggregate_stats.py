#!/usr/bin/env python3
"""
Aggregate Theory/Experiment counts and collaboration counts across several
QM2027 track Primary lists, using per-abstract metadata parsed by
extract_abstracts.py. Also separates out talks whose listed "Presenter" is
very likely a collaboration-liaison placeholder (not the eventual speaker),
so gender inference (done separately, by Claude, from the output) isn't
skewed by one convener's name standing in for a dozen different speakers.

Usage:
    python3 aggregate_stats.py tracks.json all_abstracts.json

tracks.json shape:
    {"CD": [183, 488, ...], "LC": [695, 936, ...], ...}
    (the Primary-list abstract IDs for each track tab, pulled from the
    POC tracking Google Sheet — see SKILL.md section 1)

Prints category totals, collaboration totals (Experiment talks only), and
writes two files next to the inputs:
    individual_presenters.json  - talks to hand-classify for gender
    excluded_presenters.json    - talks auto-excluded as liaison/placeholder,
                                   with the reason, for a sanity check
"""
import json
import re
import sys
from collections import Counter, defaultdict

COLLAB_NORM = {
    "STAR Collaboration": "STAR",
    "The CMS Collaboration": "CMS",
    "ALICE Collaboration": "ALICE",
    "ALICE Collaboration @ CERN": "ALICE",
    "ALICE": "ALICE",
    "HADES Collaboration": "HADES",
    "sPHENIX Collaboration": "sPHENIX",
    "JETSCAPE Collaboration": "JETSCAPE",
}

# A presenter's own talk count across the WHOLE combined set, by track, at
# or above this many distinct tracks marks them as a likely serial liaison
# rather than a real per-talk speaker commitment.
LIAISON_TRACK_THRESHOLD = 4


def clean(s):
    if not s:
        return ""
    lines = s.split("\n")
    out = []
    for l in lines:
        l = l.strip().strip("\x0c")
        if not l:
            continue
        if re.match(r"^(October|September|Quark Matter|Report of Abstracts|Page \d+)", l):
            continue
        if re.match(r"^\d+$", l):
            continue
        out.append(l)
    return " ".join(out).strip()


def main(tracks_path, abstracts_path):
    with open(tracks_path) as f:
        tracks = json.load(f)
    with open(abstracts_path) as f:
        raw = {int(k): v for k, v in json.load(f).items()}

    rows = []
    for tab, ids in tracks.items():
        for i in ids:
            d = raw.get(i)
            if d is None:
                print(f"WARNING: id {i} ({tab}) not found in {abstracts_path}")
                continue
            cat = clean(d["category"])
            collab = clean(d["collab"])
            collab = COLLAB_NORM.get(collab, collab)
            rows.append(
                {
                    "tab": tab,
                    "id": i,
                    "category": cat,
                    "collab": collab,
                    "presenter": d["presenter"].strip(),
                }
            )

    cat_counts = Counter(r["category"] for r in rows)
    print("CATEGORY TOTALS:", dict(cat_counts))

    collab_counts = Counter(
        r["collab"] for r in rows if r["category"] == "Experiment"
    )
    print("\nCOLLABORATION TOTALS (Experiment talks):")
    for k, v in collab_counts.most_common():
        print(f"  {k or '(individual / none listed)'}: {v}")

    # presenter -> set of distinct tracks they appear in
    presenter_tracks = defaultdict(set)
    for r in rows:
        presenter_tracks[r["presenter"]].add(r["tab"])

    individual, excluded = [], []
    for r in rows:
        p = r["presenter"]
        reason = None
        if not p:
            reason = "blank presenter field"
        elif p.upper() == p and (
            "COLLABORATION" in p.upper() or "CONSORTIUM" in p.upper() or "ALLIANCE" in p.upper()
        ):
            reason = "presenter IS the collaboration (all-caps collective name)"
        elif p == r["collab"]:
            reason = "presenter name equals the collaboration name"
        elif len(presenter_tracks[p]) >= LIAISON_TRACK_THRESHOLD:
            reason = (
                f"same presenter listed across {len(presenter_tracks[p])} different "
                "tracks - almost certainly a collaboration liaison standing in for "
                "a not-yet-determined speaker, not evidence this person gives all "
                "of those talks"
            )
        if reason:
            excluded.append({**r, "reason": reason})
        else:
            individual.append(r)

    print(f"\n{len(individual)} talks left for individual gender classification "
          f"({len(excluded)} excluded as collaboration-liaison/placeholder).")
    print("Classify `individual_presenters.json` by hand (or have Claude do it from "
          "the presenter's given name), marking Unknown rather than guessing on an "
          "ambiguous name - see SKILL.md section 3.")

    with open("individual_presenters.json", "w") as f:
        json.dump(individual, f, indent=1, ensure_ascii=False)
    with open("excluded_presenters.json", "w") as f:
        json.dump(excluded, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
