import json, re, html, sys

if len(sys.argv) != 4:
    print('Usage: python3 build_data.py <track_sheets.json> <full_abstracts.json> <output_tracks_full.json>')
    sys.exit(1)

with open(sys.argv[1], encoding='utf-8') as f:
    sheets = json.load(f)

with open(sys.argv[2], encoding='utf-8') as f:
    abstracts = json.load(f)  # keys are strings

TRACK_NAMES = {
    'CH': 'Chirality', 'CD': 'Collective Dynamics', 'EM': 'Electromagnetic Probes',
    'FA': 'Future Experiments & Instrumentation', 'EI': 'Electron Ion Collision Physics',
    'LC': 'Lattice & High Performance Computing', 'AQ': 'Quantum Computing & Artificial Intelligence',
    'HF': 'Heavy Flavor Physics', 'IS': 'Initial State of Particle Collisions & Intersection with Nuclear Structure',
    'JE': 'Jets', 'LF': 'Light and Strange Flavor Physics', 'NT': 'New Theoretical Developments',
    'AS': 'Nuclear Astrophysics', 'UP': 'Physics of Ultra-Peripheral Collisions',
    'CP': 'QCD at Finite Density and Temperature & Critical Point Searches',
    'SM': 'Small Systems', 'EX': 'Exotics and Heavy/Hyper-nuclei',
}
ORDER = ['CH','CD','EM','FA','EI','LC','AQ','HF','IS','JE','LF','NT','AS','UP','CP','SM','EX']

def norm_cat(v):
    v = (v or '').strip().lower()
    if v in ('experiment', 'exp'):
        return 'Experiment'
    if v in ('theory', 'th'):
        return 'Theory'
    return v.strip().title() if v.strip() else ''

def parse_tab(code, raw):
    rows = [r.split('\t') for r in raw.split('\n')]
    # strip fully-empty trailing columns per row isn't necessary; we index by header name
    poc_liaison = rows[0][0].replace('POC Liaison:', '').strip() if rows else ''
    iac_members = rows[1][0].replace('IAC POC members:', '').strip() if len(rows) > 1 else ''

    header_idx = None
    header_map = {}
    items = []
    section = None  # 'primary' | 'secondary'
    section_label = ''
    notes = []

    for i, row in enumerate(rows):
        first = row[0].strip() if row else ''
        joined = '\t'.join(row).strip()
        if not joined:
            continue
        if first.startswith('Rank') and ('Id' in row or 'ID' in row):
            header_map = {name.strip(): idx for idx, name in enumerate(row) if name.strip()}
            header_idx = i
            continue
        if re.match(r'^Oral\s*[—-]', first):
            notes_lower = first.lower()
            if 'secondary' in notes_lower:
                section = 'secondary'
            else:
                section = 'primary'
            section_label = first
            continue
        if header_idx is None:
            continue
        # data row candidate: must have something in the Id column and Rank column look numeric-ish
        id_col = header_map.get('Id')
        rank_col = header_map.get('Rank')
        if id_col is None or id_col >= len(row):
            continue
        id_val = row[id_col].strip()
        if not id_val or not re.match(r'^\d+$', id_val):
            # could be a footnote/POC-note line outside the table
            if first and section is not None and not first[0].isdigit():
                notes.append(first)
            continue
        rank_val = row[rank_col].strip() if rank_col is not None and rank_col < len(row) else ''
        def get(colname):
            idx = header_map.get(colname)
            if idx is None or idx >= len(row):
                return ''
            return row[idx].strip()

        item = {
            'rank': rank_val,
            'id': id_val,
            'title_sheet': get('Title'),
            'affiliation_sheet': get('Affiliation'),
            'category_sheet': norm_cat(get('Category')),
            'collaboration': get('Collaboration'),
            'score': get('Score'),
            'merge_with': get('Merge with'),
            'comment': get('Comment'),
            'leading_talk': get('Leading Talk 여부'),
            'loc_confirm': get('LOC Confirm'),
            'section': section or 'primary',
        }
        items.append(item)

    return {
        'code': code,
        'name': TRACK_NAMES.get(code, code),
        'poc_liaison': poc_liaison,
        'iac_members': iac_members,
        'notes': notes,
        'items': items,
    }

tracks = []
for code in ORDER:
    if code not in sheets:
        continue
    t = parse_tab(code, sheets[code])
    tracks.append(t)

# enrich with full abstract data
missing = []
for t in tracks:
    for item in t['items']:
        ab = abstracts.get(item['id'])
        if ab:
            item['title'] = ab['title'] or item['title_sheet']
            item['body'] = ab['body']
            item['authors'] = ab['authors']
            item['presenter'] = ab['presenter']
            item['category_pdf'] = ab['category']
            item['status'] = ab['status']
        else:
            item['title'] = item['title_sheet']
            item['body'] = ''
            item['authors'] = ''
            item['presenter'] = ''
            item['category_pdf'] = ''
            item['status'] = ''
            missing.append((t['code'], item['id']))

with open(sys.argv[3], 'w', encoding='utf-8') as f:
    json.dump(tracks, f, indent=1, ensure_ascii=False)

print('tracks parsed:', [(t['code'], len(t['items'])) for t in tracks])
if missing:
    print('missing abstract lookups (sheet Id not found in PDF):', missing)
