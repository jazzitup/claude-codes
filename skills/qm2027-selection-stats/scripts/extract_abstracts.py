#!/usr/bin/env python3
"""
Parse a QM2027 Indico "Book of Abstracts" PDF (already run through
`pdftotext -layout`) into a per-ID JSON of {category, collab, affil,
presenter, author}.

Usage:
    pdftotext -layout QM2027_abstracts_all_<date>.pdf all.txt
    python3 extract_abstracts.py all.txt all_abstracts.json
"""
import re
import json
import sys


def parse(text_path):
    with open(text_path) as f:
        text = f.read()

    blocks = re.split(r"\nAbstract ID : (\d+)\n", text)
    data = {}
    for i in range(1, len(blocks), 2):
        aid = int(blocks[i])
        content = blocks[i + 1]

        def grab(label, stop_labels):
            pat = (
                r"\n"
                + re.escape(label)
                + r"\n(.*?)(?="
                + "|".join(r"\n" + re.escape(s) + r"\n" for s in stop_labels)
                + ")"
            )
            m = re.search(pat, content, re.S)
            return m.group(1).strip() if m else ""

        category = grab("Category", ["Is this a collaboration presentation?"])
        collab = grab(
            "If yes, please enter the collaboration name.", ["Funding (Optional)"]
        )
        affil = grab("Affiliation", ["Country"])
        m2 = re.search(r"\nPresenter:\s*(.+?)\n", content)
        presenter = m2.group(1).strip() if m2 else ""
        m3 = re.search(r"\nAuthor:\s*(.+?)\n", content)
        author = m3.group(1).strip() if m3 else ""
        data[aid] = {
            "category": category,
            "collab": collab,
            "affil": affil,
            "presenter": presenter,
            "author": author,
        }
    return data


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    data = parse(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        json.dump(data, f)
    print(f"parsed {len(data)} abstracts -> {sys.argv[2]}")
