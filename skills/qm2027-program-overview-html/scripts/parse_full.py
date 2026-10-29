import re, json, sys

if len(sys.argv) != 3:
    print('Usage: python3 parse_full.py <pdftotext_layout_output.txt> <output_full_abstracts.json>')
    sys.exit(1)

with open(sys.argv[1]) as f:
    text = f.read()

blocks = re.split(r'\nAbstract ID : (\d+)\n', text)
data = {}

def clean_footer(s):
    lines = s.split('\n')
    out = []
    for l in lines:
        l = l.strip().strip('\x0c')
        if not l:
            continue
        if re.match(r'^(October|September|Quark Matter|Report of Abstracts|Page \d+)', l):
            continue
        if re.match(r'^\d+$', l):
            continue
        out.append(l)
    return ' '.join(out).strip()

for i in range(1, len(blocks), 2):
    aid = int(blocks[i])
    content = blocks[i+1]

    # Title: between the ID line and "Content"
    m_title = re.search(r'^(.*?)\nContent\n', content, re.S)
    title_raw = m_title.group(1) if m_title else ''
    title = clean_footer(title_raw)

    # Abstract body: between "Content" and "Affiliation"
    m_body = re.search(r'\nContent\n(.*?)\nAffiliation\n', content, re.S)
    body = clean_footer(m_body.group(1)) if m_body else ''

    m_cat = re.search(r'\nCategory\n(.*?)\nIs this a collaboration presentation\?', content, re.S)
    cat_raw = m_cat.group(1) if m_cat else ''
    if 'Theory' in cat_raw and 'Experiment' in cat_raw:
        category = 'Ambiguous'
    elif 'Theory' in cat_raw:
        category = 'Theory'
    elif 'Experiment' in cat_raw:
        category = 'Experiment'
    else:
        category = ''

    m_collab = re.search(r'If yes, please enter the collaboration name\.\n(.*?)\nFunding', content, re.S)
    collab = clean_footer(m_collab.group(1)) if m_collab else ''

    m_authors = re.search(r'\nAuthors:\s*(.+?)\n\nPresenter:', content, re.S)
    authors = clean_footer(m_authors.group(1)) if m_authors else ''

    m_presenter = re.search(r'\nPresenter:\s*(.+?)\n', content)
    presenter = m_presenter.group(1).strip() if m_presenter else ''

    m_track = re.search(r'Track Classification:\s*(.+?)(?:\n\n|\nContribution Type:)', content, re.S)
    track_raw = m_track.group(1).strip() if m_track else ''
    track = re.split(r'\s*\(', track_raw)[0].strip()
    track = re.sub(r'\s+', ' ', track).replace('&amp;', '&')

    m_type = re.search(r'Contribution Type:\s*(.+?)\n', content)
    ctype = m_type.group(1).strip() if m_type else ''

    m_status = re.search(r'Status:\s*(\S+)', content)
    status = m_status.group(1).strip() if m_status else ''

    data[aid] = {
        'title': title,
        'body': body,
        'category': category,
        'collab': collab,
        'authors': authors,
        'presenter': presenter,
        'track': track,
        'type': ctype,
        'status': status,
    }

with open(sys.argv[2], 'w') as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

print('parsed', len(data), 'abstracts ->', sys.argv[2])
