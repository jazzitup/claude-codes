import json, html, re, sys

if len(sys.argv) != 3:
    print('Usage: python3 build_html.py <tracks_full.json> <output.html>')
    sys.exit(1)

with open(sys.argv[1], encoding='utf-8') as f:
    tracks = json.load(f)

def esc(s):
    return html.escape(s or '', quote=True)

def nl2br(s):
    return esc(s).replace('\n', '<br>')

CSS = """
:root{
  --bg:#ffffff; --fg:#1a1a1a; --muted:#6b7280; --border:#e5e7eb; --card:#f7f7f8;
  --primary-bg:#fde3e3; --primary-bg-dark:#3a2222; --secondary-bg:#dce9fb; --secondary-bg-dark:#1f2b3d;
  --accent:#2563eb; --theory:#6d28d9; --experiment:#0f766e; --detail-bg:#fafafa;
}
@media (prefers-color-scheme: dark){
  :root{ --bg:#0f1115; --fg:#e8e8ea; --muted:#9aa0a6; --border:#2a2e37; --card:#171a21;
  --primary-bg:#3a2222; --secondary-bg:#1f2b3d; --accent:#60a5fa; --theory:#c4b5fd; --experiment:#5eead4; --detail-bg:#12141a; }
}
*{box-sizing:border-box;}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;margin:0;padding:0 16px 80px;line-height:1.5;}
.wrap{max-width:1100px;margin:0 auto;}
h1{font-size:1.6rem;margin:2rem 0 .25rem;}
.subtitle{color:var(--muted);font-size:.92rem;margin-bottom:1.5rem;}
.toc{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:1rem 1.25rem;margin-bottom:2rem;}
.toc h2{font-size:1rem;margin:0 0 .6rem;}
.toc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:4px 12px;}
.toc-grid a{color:var(--accent);text-decoration:none;font-size:.88rem;}
.toc-grid a:hover{text-decoration:underline;}
section.track{margin:2.5rem 0;scroll-margin-top:1rem;}
.track-head{display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap;border-bottom:2px solid var(--border);padding-bottom:.5rem;margin-bottom:.25rem;}
.track-head h2{font-size:1.25rem;margin:0;}
.track-code{font-size:.8rem;color:var(--muted);font-weight:600;background:var(--card);padding:1px 8px;border-radius:999px;}
.track-meta{color:var(--muted);font-size:.85rem;margin:.3rem 0 .8rem;}
.track-empty{color:var(--muted);font-size:.9rem;font-style:italic;padding:.5rem 0 1rem;}
table.items{width:100%;border-collapse:collapse;font-size:.88rem;margin-bottom:.4rem;}
table.items th{text-align:left;padding:6px 8px;color:var(--muted);font-size:.74rem;text-transform:uppercase;letter-spacing:.03em;border-bottom:1px solid var(--border);}
table.items td{padding:6px 8px;border-bottom:1px solid var(--border);vertical-align:top;}
tr.row-primary > td{background:var(--primary-bg);}
tr.row-secondary > td{background:var(--secondary-bg);}
td.num{text-align:right;font-variant-numeric:tabular-nums;width:1%;white-space:nowrap;padding-right:4px;}
td.idcol{font-variant-numeric:tabular-nums;width:1%;white-space:nowrap;padding-left:4px;padding-right:4px;}
td.titlecol{white-space:normal;}
.title-line{font-weight:500;}
.meta-line{margin-top:3px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
.meta-line .collab-name{font-size:.82rem;color:var(--muted);}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.78rem;font-weight:600;}
.pill.theory{background:color-mix(in srgb, var(--theory) 18%, transparent);color:var(--theory);}
.pill.experiment{background:color-mix(in srgb, var(--experiment) 18%, transparent);color:var(--experiment);}
button.toggle{cursor:pointer;border:1px solid var(--border);background:var(--bg);color:var(--fg);border-radius:6px;padding:3px 10px;font-size:.8rem;}
button.toggle:hover{border-color:var(--accent);color:var(--accent);}
tr.detail-row{display:none;}
tr.detail-row.open{display:table-row;}
tr.detail-row > td{background:var(--detail-bg);padding:14px 18px;border-bottom:1px solid var(--border);}
.detail-title{font-weight:700;margin-bottom:.4rem;font-size:.98rem;}
.detail-field{margin:.35rem 0;font-size:.86rem;}
.detail-field b{color:var(--muted);font-weight:600;margin-right:.3rem;}
.detail-body{margin-top:.6rem;font-size:.86rem;white-space:normal;}
.legend{display:flex;gap:1.2rem;align-items:center;font-size:.82rem;color:var(--muted);margin:.4rem 0 1rem;flex-wrap:wrap;}
.legend-swatch{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px;}
.footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--border);color:var(--muted);font-size:.8rem;}
"""

JS = """
function toggleDetail(id){
  var row = document.getElementById(id);
  if (row) row.classList.toggle('open');
}
"""

def cat_pill(cat):
    if not cat:
        return ''
    cls = 'theory' if cat == 'Theory' else ('experiment' if cat == 'Experiment' else '')
    return f'<span class="pill {cls}">{esc(cat)}</span>'

def render_item(track_code, idx, item):
    detail_id = f"detail-{track_code}-{idx}"
    section_cls = 'row-primary' if item['section'] == 'primary' else 'row-secondary'
    cat = item.get('category_pdf') or item.get('category_sheet') or ''
    collab = item.get('collaboration') or ''
    title = item.get('title') or item.get('title_sheet') or ''
    row = f"""
<tr class="{section_cls}">
  <td class="num">{esc(item['rank'])}</td>
  <td class="idcol">{esc(item['id'])}</td>
  <td class="titlecol">
    <div class="title-line">{esc(title)}</div>
    <div class="meta-line">{cat_pill(cat)}{f'<span class="collab-name">{esc(collab)}</span>' if collab else ''}</div>
  </td>
  <td><button class="toggle" onclick="toggleDetail('{detail_id}')">abstract ▾</button></td>
</tr>"""

    authors = item.get('authors') or ''
    presenter = collab if collab else (item.get('presenter') or '')
    affiliation = item.get('affiliation_sheet') or ''
    body = item.get('body') or ''
    score = item.get('score') or ''
    merge_with = item.get('merge_with') or ''
    comment = item.get('comment') or ''
    leading = item.get('leading_talk') or ''
    status = item.get('status') or ''

    fields = []
    if presenter:
        fields.append(f"<div class='detail-field'><b>Presenter</b>{esc(presenter)}</div>")
    if authors:
        fields.append(f"<div class='detail-field'><b>Authors</b>{esc(authors)}</div>")
    if affiliation:
        fields.append(f"<div class='detail-field'><b>Affiliation (sheet)</b>{esc(affiliation)}</div>")
    if score:
        fields.append(f"<div class='detail-field'><b>Score</b>{esc(score)}</div>")
    if leading:
        fields.append(f"<div class='detail-field'><b>Leading Talk</b>{esc(leading)}</div>")
    if merge_with:
        fields.append(f"<div class='detail-field'><b>Merge suggestion</b>{esc(merge_with)}</div>")
    if comment:
        fields.append(f"<div class='detail-field'><b>Comment</b>{nl2br(comment)}</div>")
    if status and status != 'SUBMITTED':
        fields.append(f"<div class='detail-field'><b>Status</b>{esc(status)}</div>")

    detail = f"""
<tr class="detail-row" id="{detail_id}">
  <td colspan="4">
    <div class="detail-title">#{esc(item['id'])} — {esc(title)}</div>
    {''.join(fields)}
    <div class="detail-body">{nl2br(body) if body else '<i>(abstract text not found)</i>'}</div>
  </td>
</tr>"""
    return row + detail

def render_track(t):
    code = t['code']
    items = t['items']
    primary = [it for it in items if it['section'] == 'primary']
    secondary = [it for it in items if it['section'] == 'secondary']
    rows_html = []
    for idx, it in enumerate(primary):
        rows_html.append(render_item(code, f"p{idx}", it))
    for idx, it in enumerate(secondary):
        rows_html.append(render_item(code, f"s{idx}", it))

    if not items:
        body = f"<div class='track-empty'>아직 선정 결과가 입력되지 않았습니다 (POC Liaison: {esc(t['poc_liaison'])}).</div>"
    else:
        notes_html = ''
        if t['notes']:
            notes_html = '<div class="track-meta">' + '<br>'.join(esc(n) for n in t['notes']) + '</div>'
        body = f"""
<div class="legend">
  <span><span class="legend-swatch" style="background:var(--primary-bg)"></span>Primary ({len(primary)})</span>
  <span><span class="legend-swatch" style="background:var(--secondary-bg)"></span>Secondary ({len(secondary)})</span>
</div>
<table class="items">
<thead><tr><th>Rank</th><th>Id</th><th>Title, Category, Collaboration</th><th></th></tr></thead>
<tbody>
{''.join(rows_html)}
</tbody>
</table>
{notes_html}
"""

    return f"""
<section class="track" id="track-{code}">
  <div class="track-head">
    <h2>{esc(t['name'])}</h2>
    <span class="track-code">{esc(code)}</span>
  </div>
  <div class="track-meta">POC Liaison: {esc(t['poc_liaison'])}</div>
  {body}
</section>
"""

toc_links = ''.join(
    f'<a href="#track-{t["code"]}">{esc(t["code"])} — {esc(t["name"])} ({len(t["items"])})</a>'
    for t in tracks
)

sections_html = ''.join(render_track(t) for t in tracks)

total_items = sum(len(t['items']) for t in tracks)

html_out = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QM2027 Parallel Talk Selection — Program Overview</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<h1>QM2027 Parallel Talk Selection — Program Overview</h1>
<p class="subtitle">17개 트랙(program)별 POC 선정 결과. Primary list(90%)와 Secondary candidate를 색으로 구분했고, 각 행의 "abstract ▾" 버튼을 누르면 해당 발표의 전체 abstract와 POC 코멘트(Merge 제안 포함)를 볼 수 있습니다. 총 {total_items}건.</p>
<div class="toc">
<h2>Tracks</h2>
<div class="toc-grid">{toc_links}</div>
</div>
{sections_html}
<div class="footer">
  Source: "POC's parallel selection" Google Sheet (per-track tabs) + QM2027_abstracts_all_2026-10-24.pdf. 생성일: 2026-10-29.
</div>
</div>
<script>{JS}</script>
</body>
</html>
"""

out_path = sys.argv[2]
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html_out)

print('wrote', out_path, len(html_out), 'bytes')
