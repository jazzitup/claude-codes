#!/usr/bin/env python3
"""Render an Indico registration/abstract stats dashboard from a JSON summary.

Usage:
    python3 build_report.py --input data.json --output report.html

No third-party dependencies. See ../SKILL.md for the JSON schema and the
data-collection workflow this consumes.
"""
import argparse
import html
import json

PALETTE_SERIES = ["--series-1", "--series-2", "--series-3", "--series-4", "--series-5", "--series-6"]

CSS = """
:root {
  color-scheme: light;
  --surface-1:      #fcfcfb;
  --page-plane:     #f9f9f7;
  --text-primary:   #0b0b0b;
  --text-secondary: #52514e;
  --text-muted:     #898781;
  --gridline:       #e1e0d9;
  --border:         rgba(11,11,11,0.10);
  --good:           #0ca30c;
  --warning:        #fab219;
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a;
  --series-4: #eda100; --series-5: #e87ba4; --series-6: #4a3aa7;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --surface-1: #1a1a19; --page-plane: #0d0d0d;
    --text-primary: #ffffff; --text-secondary: #c3c2b7; --text-muted: #898781;
    --gridline: #2c2c2a; --border: rgba(255,255,255,0.10);
    --good: #0ca30c; --warning: #fab219;
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
    --series-4: #c98500; --series-5: #d55181; --series-6: #9085e9;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --surface-1: #1a1a19; --page-plane: #0d0d0d;
  --text-primary: #ffffff; --text-secondary: #c3c2b7; --text-muted: #898781;
  --gridline: #2c2c2a; --border: rgba(255,255,255,0.10);
  --good: #0ca30c; --warning: #fab219;
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70;
  --series-4: #c98500; --series-5: #d55181; --series-6: #9085e9;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--page-plane); color: var(--text-primary);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  padding: 32px 20px 60px;
}
.wrap { max-width: 920px; margin: 0 auto; }
header h1 { font-size: 1.5rem; margin: 0 0 4px; }
header .sub { color: var(--text-secondary); font-size: 0.95rem; margin: 0 0 2px; }
header .meta { color: var(--text-muted); font-size: 0.85rem; margin: 0 0 24px; }
.card {
  background: var(--surface-1); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;
}
.card h2 { font-size: 1.05rem; margin: 0 0 16px; }
.card h2 .asof { color: var(--text-muted); font-weight: 400; font-size: 0.8rem; }
.tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 18px 20px; }
.tile .value { font-size: 2.1rem; font-weight: 600; line-height: 1; font-variant-numeric: proportional-nums; }
.tile .label { color: var(--text-secondary); font-size: 0.85rem; margin-top: 6px; }
.tile .sub { color: var(--text-muted); font-size: 0.78rem; margin-top: 2px; }
.bars { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: grid; grid-template-columns: 220px 1fr 70px; align-items: center; gap: 10px; }
.bar-row .cat { font-size: 0.85rem; text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { background: var(--gridline); border-radius: 4px; height: 16px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; }
.bar-row .num { font-size: 0.85rem; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--gridline); white-space: nowrap; }
th { color: var(--text-muted); font-weight: 500; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.02em; }
td.title-cell, th.title-cell { white-space: normal; }
tr:last-child td { border-bottom: none; }
.table-scroll { overflow-x: auto; }
.pill { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 0.75rem; font-weight: 500; }
.pill.good { background: color-mix(in srgb, var(--good) 16%, transparent); color: var(--good); }
.pill.warn { background: color-mix(in srgb, var(--warning) 22%, transparent); color: #8a5a00; }
.pill.muted { background: var(--gridline); color: var(--text-muted); }
:root[data-theme="dark"] .pill.warn { color: var(--warning); }
@media (prefers-color-scheme: dark) { :root:where(:not([data-theme="light"])) .pill.warn { color: var(--warning); } }
footer { color: var(--text-muted); font-size: 0.78rem; margin-top: 24px; text-align: center; }
footer a { color: inherit; }
@media (max-width: 640px) {
  .tiles { grid-template-columns: 1fr; }
  .bar-row { grid-template-columns: 110px 1fr 56px; }
}
"""

STATE_PILL = {
    "completed": "good",
    "awaiting review": "muted",
    "withdrawn": "muted",
}


def esc(s):
    return html.escape(str(s), quote=True)


def pill_class(state):
    return STATE_PILL.get(str(state).strip().lower(), "warn")


def bar_group(counts, color_cycle=True):
    """counts: ordered dict/list of (label, value). Renders bar rows."""
    items = list(counts.items()) if isinstance(counts, dict) else list(counts)
    if not items:
        return "<p style=\"color:var(--text-secondary); font-size:0.85rem;\">데이터 없음</p>"
    maxv = max(v for _, v in items) or 1
    rows = []
    for i, (label, value) in enumerate(items):
        pct = round(100 * value / maxv, 1)
        color = f"var({PALETTE_SERIES[i % len(PALETTE_SERIES)]})"
        rows.append(
            f'<div class="bar-row"><div class="cat">{esc(label)}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%; background:{color}"></div></div>'
            f'<div class="num">{value}</div></div>'
        )
    return '<div class="bars">' + "".join(rows) + "</div>"


def pct_table(counts, total, extra_col=None, extra_label="비고"):
    items = list(counts.items()) if isinstance(counts, dict) else list(counts)
    header = f"<tr><th>항목</th><th>건수</th><th>비율</th>{'<th>' + esc(extra_label) + '</th>' if extra_col else ''}</tr>"
    rows = []
    for label, value in items:
        pct = f"{100 * value / total:.1f}%" if total else "—"
        extra = f"<td>{esc(extra_col.get(label, ''))}</td>" if extra_col else ""
        rows.append(f"<tr><td>{esc(label)}</td><td>{value}</td><td>{pct}</td>{extra}</tr>")
    rows.append(
        f"<tr><td><strong>합계</strong></td><td><strong>{sum(v for _, v in items)}</strong></td>"
        f"<td><strong>{'100%' if total else '—'}</strong></td>{'<td></td>' if extra_col else ''}</tr>"
    )
    return f'<div class="table-scroll"><table><thead>{header}</thead><tbody>{"".join(rows)}</tbody></table></div>'


def registration_table(roster, redact_emails=True):
    cols = ["ID", "이름", "소속", "국가", "유형", "등록일", "상태"]
    header = "".join(f"<th>{esc(c)}</th>" for c in cols)
    rows = []
    for r in roster:
        name = esc(r.get('name',''))
        if r.get('duplicate_note'):
            name += f' <span class="pill muted">{esc(r["duplicate_note"])}</span>'
        rows.append(
            "<tr>"
            f"<td>{esc(r.get('id',''))}</td>"
            f"<td>{name}</td>"
            f"<td>{esc(r.get('affiliation',''))}</td>"
            f"<td>{esc(r.get('country',''))}</td>"
            f"<td>{esc(r.get('position',''))}</td>"
            f"<td>{esc(r.get('date',''))}</td>"
            f'<td><span class="pill {pill_class(r.get("state",""))}">{esc(r.get("state",""))}</span></td>'
            "</tr>"
        )
    return f'<div class="table-scroll"><table><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def comparison_card(cmp, reg, ab):
    prev_as_of = esc(cmp.get("as_of", "이전 리포트"))
    prev_reg = cmp.get("registration", {}) or {}
    prev_ab = cmp.get("abstracts", {}) or {}

    tiles = []
    if "active_count" in prev_reg:
        cur = reg.get("active_count", 0)
        prev = prev_reg["active_count"]
        delta = cur - prev
        sign = "+" if delta > 0 else ("±0" if delta == 0 else "")
        color = "var(--good)" if delta > 0 else ("var(--text-primary)" if delta == 0 else "var(--warning)")
        tiles.append(f"""
      <div class="tile">
        <div class="value" style="color:{color};">{sign if delta==0 else f"{sign}{delta}"}</div>
        <div class="label">등록 인원 (활성)</div>
        <div class="sub">{prev}건 → {cur}건</div>
      </div>""")
    if "total" in prev_ab:
        cur = ab.get("total", 0)
        prev = prev_ab["total"]
        delta = cur - prev
        sign = "+" if delta > 0 else ("±0" if delta == 0 else "")
        color = "var(--good)" if delta > 0 else ("var(--text-primary)" if delta == 0 else "var(--warning)")
        tiles.append(f"""
      <div class="tile">
        <div class="value" style="color:{color};">{sign if delta==0 else f"{sign}{delta}"}</div>
        <div class="label">제출된 초록</div>
        <div class="sub">{prev}건 → {cur}건</div>
      </div>""")

    track_rows = ""
    prev_track = prev_ab.get("by_track")
    if prev_track:
        cur_track = ab.get("by_track", {})
        labels = list(dict.fromkeys(list(prev_track.keys()) + list(cur_track.keys())))
        rows = []
        for label in labels:
            p, c = prev_track.get(label, 0), cur_track.get(label, 0)
            if p == c:
                continue
            d = c - p
            rows.append(f"<tr><td>{esc(label)}</td><td>{p}</td><td>{c}</td><td>{'+' if d>0 else ''}{d}</td></tr>")
        if rows:
            track_rows = (
                '<div class="table-scroll" style="margin-top:14px;"><table>'
                "<thead><tr><th>트랙</th><th>이전</th><th>현재</th><th>변화</th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table></div>"
            )

    new_items = cmp.get("new_abstracts") or []
    new_table = ""
    if new_items:
        new_table = (
            '<h2 style="margin-top:22px; font-size:0.95rem;">신규 제출 초록</h2>'
            + abstract_table(new_items)
        )

    note = f'<p style="color:var(--text-secondary); font-size:0.85rem; margin:16px 0 0;">{esc(cmp["note"])}</p>' if cmp.get("note") else ""

    return (
        f'<div class="card"><h2>지난 리포트({prev_as_of}) 대비 변화</h2>'
        f'<div class="tiles" style="margin-bottom:0;">{"".join(tiles)}</div>'
        f"{track_rows}{note}{new_table}</div>"
    )


def crossref_card(crossref, unmatched_note):
    rows = []
    for c in crossref:
        rows.append(
            "<tr>"
            f"<td>{esc(c.get('reg_id',''))}</td>"
            f"<td>{esc(c.get('name',''))}</td>"
            f"<td>{esc(c.get('abstract_id',''))}</td>"
            f"<td>{esc(c.get('category',''))}</td>"
            "</tr>"
        )
    table = (
        '<div class="table-scroll"><table><thead><tr><th>등록 ID</th><th>이름</th><th>대조된 초록</th><th>카테고리</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )
    note = f'<p style="color:var(--text-secondary); font-size:0.85rem; margin:12px 0 0;">{esc(unmatched_note)}</p>' if unmatched_note else ""
    return (
        '<div class="card"><h2>등록자 Theory / Experiment</h2>'
        '<p style="color:var(--text-secondary); font-size:0.85rem; margin:0 0 12px;">'
        "등록 양식 자체에는 Theory/Experiment 구분 필드가 없음. 초록 제출자 이름을 대조한 결과만 표시하며, "
        "나머지는 초록 미제출/이름 불일치로 분류 불가(추정하지 않음).</p>"
        f"{table}{note}</div>"
    )


def abstract_table(items):
    cols = ["ID", "제목", "트랙", "카테고리", "국가", "유형", "상태"]
    header = "".join(f'<th class="title-cell">{esc(c)}</th>' if c == "제목" else f"<th>{esc(c)}</th>" for c in cols)
    rows = []
    for a in items:
        rows.append(
            "<tr>"
            f"<td>{esc(a.get('id',''))}</td>"
            f"<td class=\"title-cell\">{esc(a.get('title',''))}</td>"
            f"<td>{esc(a.get('track',''))}</td>"
            f"<td>{esc(a.get('category',''))}</td>"
            f"<td>{esc(a.get('country','—'))}</td>"
            f"<td>{esc(a.get('type',''))}</td>"
            f'<td><span class="pill {pill_class(a.get("state",""))}">{esc(a.get("state",""))}</span></td>'
            "</tr>"
        )
    return f'<div class="table-scroll"><table><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def build(data):
    ev = data.get("event", {})
    reg = data.get("registration", {})
    ab = data.get("abstracts", {})
    redact = data.get("redact_emails", True)

    active = reg.get("active_count", 0)
    submitted = reg.get("total_submitted", active)
    withdrawn = submitted - active

    tiles = f"""
    <div class="tiles">
      <div class="tile">
        <div class="value">{active}</div>
        <div class="label">등록 인원 (활성)</div>
        <div class="sub">전체 제출 {submitted}건 중 철회 {withdrawn}건 제외</div>
      </div>
      <div class="tile">
        <div class="value">{ab.get('total', 0)}</div>
        <div class="label">제출된 초록</div>
        <div class="sub">{esc(ev.get('as_of', ''))} 기준</div>
      </div>
      <div class="tile">
        <div class="value">{esc(ab.get('deadline', '미정').split(' ')[0] if ab.get('deadline') else '미정')}</div>
        <div class="label">초록 접수 마감</div>
        <div class="sub">{esc(ab.get('deadline', ''))}</div>
      </div>
    </div>
    """

    parts = [tiles]

    if data.get("comparison"):
        parts.append(comparison_card(data["comparison"], reg, ab))

    if reg.get("by_state"):
        parts.append(f"""<div class="card"><h2>등록 상태 분포 <span class="asof">{esc(ev.get('as_of',''))} 기준</span></h2>{bar_group(reg['by_state'])}</div>""")

    if reg.get("by_country") or reg.get("by_position"):
        section = f'<div class="card"><h2>등록자 국가 분포 <span class="asof">활성 {active}건 기준</span></h2>{bar_group(reg.get("by_country", {}))}'
        if reg.get("by_position"):
            section += f'<h2 style="margin-top:22px;">등록자 소속 유형 분포</h2>{bar_group(reg["by_position"])}'
        section += "</div>"
        parts.append(section)

    if ab.get("by_track"):
        total_ab = ab.get("total") or sum(ab["by_track"].values())
        parts.append(
            f'<div class="card"><h2>초록 트랙별 제출 현황 <span class="asof">전체 {total_ab}건</span></h2>'
            f'{bar_group(ab["by_track"])}'
            f'<div style="margin-top:16px;">{pct_table(ab["by_track"], total_ab)}</div></div>'
        )

    if reg.get("crossref"):
        parts.append(crossref_card(reg["crossref"], reg.get("crossref_unmatched_note", "")))

    if reg.get("roster"):
        parts.append(f'<div class="card"><h2>등록자 명단 (ID 순)</h2>{registration_table(reg["roster"], redact)}</div>')

    if ab.get("by_category") or ab.get("by_country"):
        total_ab = ab.get("total") or sum(ab.get("by_category", {}).values())
        section = '<div class="card">'
        if ab.get("by_category"):
            section += f'<h2>초록 카테고리 (Theory / Experiment)</h2>{bar_group(ab["by_category"])}'
        if ab.get("by_country"):
            section += f'<h2 style="margin-top:22px;">초록 발표자 소속 국가</h2>{pct_table(ab["by_country"], None)}'
            if ab.get("country_note"):
                section += f'<p style="color:var(--text-secondary); font-size:0.82rem; margin:12px 0 0;">{esc(ab["country_note"])}</p>'
        section += "</div>"
        parts.append(section)

    if ab.get("list"):
        parts.append(f'<div class="card"><h2>제출된 초록 목록</h2>{abstract_table(ab["list"])}</div>')

    body = "\n".join(parts)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{esc(ev.get('title', 'Indico'))} — 등록/초록 현황</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{esc(ev.get('title', ''))}</h1>
    <p class="sub">{esc(ev.get('subtitle', ''))}</p>
    <p class="meta">{esc(ev.get('dates', ''))} · {esc(ev.get('venue', ''))}</p>
  </header>
  {body}
  <footer>
    {f'<a href="{esc(ev.get("indico_url"))}" target="_blank">Indico 관리 페이지</a>에서 ' if ev.get('indico_url') else ''}{esc(ev.get('as_of', ''))} 조회 · 이메일 주소 등 개인정보는 이 요약본에서 제외함
  </footer>
</div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON summary file (see SKILL.md schema)")
    parser.add_argument("--output", required=True, help="Output HTML path")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    html_out = build(data)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
