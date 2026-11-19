#!/usr/bin/env python3
"""CapCut 데스크톱 draft를 Dropbox로 내보내고(push) 다른 Mac에서 불러온다(pull).

push <draft이름> [--dest DIR]   : draft 폴더(캐시 Resources/audioAlg 제외) + draft가 참조하는
                                   CapCut 공용 파일(Presets/Cache/다른 draft의 matting 등)을 패키지로 복사
pull <패키지 경로 또는 draft이름> : 패키지를 이 Mac의 CapCut draft 폴더로 복사, 절대경로를 이 Mac 기준으로
                                   바꾸고 root_meta_info.json에 등록. CapCut은 반드시 종료된 상태여야 함.
list                             : Dropbox에 있는 패키지 목록
"""
import sys, os, json, glob, shutil, subprocess, argparse, time
HOME = os.path.expanduser('~')
UD = os.path.join(HOME, 'Movies/CapCut/User Data')
DR = os.path.join(UD, 'Projects/com.lveditor.draft')
def dropbox_root():
    c = glob.glob(os.path.join(HOME, 'Library/CloudStorage/Dropbox*')) + [os.path.join(HOME, 'Dropbox')]
    for p in c:
        if os.path.isdir(p): return p
    sys.exit('Dropbox 폴더를 찾지 못함')
PKG_HOME_REL = os.environ.get('CAPCUT_PKG_DIR', 'K 고분 헌터스/_CapCut 편집 프로젝트')  # Dropbox 루트 기준
EXCLUDE = ['Resources/audioAlg']           # 다시 생성되는 오디오 분석 캐시(수 GB, draft_info에서 참조 안 함)
TEXT_EXT = ('.json', '.tmp', '.bak', '.extra')

def rsync(src, dst, excludes=()):
    os.makedirs(dst, exist_ok=True)
    cmd = ['rsync', '-a', '--delete'] + sum([['--exclude', e] for e in excludes], []) + [src.rstrip('/') + '/', dst]
    subprocess.run(cmd, check=True)

def text_files(d):
    for r, _, fs in os.walk(d):
        for f in fs:
            if f.endswith(TEXT_EXT) or f in ('draft_settings',):
                yield os.path.join(r, f)

def find_paths(d, prefix):
    import re
    pat = re.compile(re.escape(json.dumps(prefix)[1:-1]) + r'[^"]*')
    out = set()
    for f in text_files(d):
        try: s = open(f, encoding='utf-8').read()
        except Exception: continue
        out |= set(pat.findall(s))
    return out

def push(name, dest):
    src = os.path.join(DR, name)
    assert os.path.isdir(src), f'draft 없음: {src}'
    pkg = os.path.join(dest, name)
    rsync(src, os.path.join(pkg, 'draft'), EXCLUDE)
    # draft 밖의 CapCut 공용 파일(효과 캐시, 프리셋, 다른 draft 파일 등) 같이 담기
    extra = os.path.join(pkg, 'userdata_extra'); n = 0
    for p in find_paths(src, UD + '/'):
        p = p.replace('\\/', '/')
        if p.startswith(src + '/') or p == src or not os.path.exists(p): continue
        rel = os.path.relpath(p, UD)
        # draft 루트·다른 draft 폴더 통째·root_meta 같은 것은 담지 않는다(파일, 또는 Cache/Presets 아래 폴더만)
        if os.path.isdir(p) and (rel.startswith('Projects') or rel.count('/') < 2): continue
        if os.path.basename(p).startswith('root_meta_info'): continue
        t = os.path.join(extra, rel)
        os.makedirs(os.path.dirname(t), exist_ok=True)
        (shutil.copytree(p, t, dirs_exist_ok=True) if os.path.isdir(p) else shutil.copy2(p, t)); n += 1
    meta = json.load(open(os.path.join(DR, 'root_meta_info.json')))
    entry = next(e for e in meta['all_draft_store'] if e.get('draft_name') == name)
    info = {'name': name, 'src_home': HOME, 'src_dropbox': dropbox_root(), 'entry': entry,
            'pushed_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'host': os.uname().nodename}
    json.dump(info, open(os.path.join(pkg, 'package.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'push 완료: {pkg} (공용 파일 {n}개 포함)')

def rewrite(d, pairs):
    for f in text_files(d):
        try: s = open(f, encoding='utf-8').read()
        except Exception: continue
        t = s
        for a, b in pairs:
            t = t.replace(a, b).replace(json.dumps(a)[1:-1], json.dumps(b)[1:-1])
        if t != s: open(f, 'w', encoding='utf-8').write(t)

def pull(arg):
    pkg = arg if os.path.isdir(arg) else os.path.join(dropbox_root(), PKG_HOME_REL, arg)
    info = json.load(open(os.path.join(pkg, 'package.json')))
    if subprocess.run(['pgrep', '-x', 'CapCut'], capture_output=True).returncode == 0:
        sys.exit('CapCut이 실행 중입니다. 완전히 종료(Cmd+Q)한 뒤 다시 실행하세요.')
    name = info['name']; dst = os.path.join(DR, name)
    if os.path.isdir(dst):
        bk = dst + '.bak-' + time.strftime('%Y%m%d-%H%M%S'); shutil.move(dst, bk); print('기존 draft 백업:', bk)
    rsync(os.path.join(pkg, 'draft'), dst)
    ex = os.path.join(pkg, 'userdata_extra')
    if os.path.isdir(ex):
        subprocess.run(['rsync', '-a', '--ignore-existing', ex + '/', UD + '/'], check=True)
    pairs = []
    if info['src_dropbox'] != dropbox_root(): pairs.append((info['src_dropbox'], dropbox_root()))
    if info['src_home'] != HOME: pairs.append((info['src_home'] + '/', HOME + '/'))
    rewrite(dst, pairs)
    rmp = os.path.join(DR, 'root_meta_info.json')
    meta = json.load(open(rmp)) if os.path.exists(rmp) else {'all_draft_store': [], 'draft_ids': 0, 'root_path': DR}
    shutil.copy2(rmp, rmp + '.bak-sync') if os.path.exists(rmp) else None
    e = json.loads(json.dumps(info['entry']))
    for k in ('draft_cover', 'draft_fold_path', 'draft_json_file', 'draft_root_path'):
        if k in e:
            for a, b in pairs: e[k] = e[k].replace(a, b)
    e['draft_fold_path'] = dst; e['draft_root_path'] = DR
    e['draft_json_file'] = os.path.join(dst, 'draft_info.json'); e['draft_cover'] = os.path.join(dst, 'draft_cover.jpg')
    e['tm_draft_modified'] = int(time.time() * 1e6)
    meta['all_draft_store'] = [x for x in meta['all_draft_store'] if x.get('draft_id') != e['draft_id'] and x.get('draft_name') != name]
    meta['all_draft_store'].insert(0, e)
    json.dump(meta, open(rmp, 'w'), ensure_ascii=False)
    # 원본 영상이 이 Mac에 실제로 있는지 확인
    missing = [p for p in find_paths(dst, dropbox_root()) if not os.path.exists(p.replace('\\/', '/'))]
    print(f'pull 완료: {dst}')
    if missing: print('경고: 아직 없는 미디어(Dropbox 동기화 대기?)', *sorted(missing)[:20], sep='\n  ')

def lst():
    for p in sorted(glob.glob(os.path.join(dropbox_root(), PKG_HOME_REL, '*', 'package.json'))):
        i = json.load(open(p)); print(f"{i['name']}\t{i['pushed_at']}\t{i['host']}")

ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
a = sp.add_parser('push'); a.add_argument('name'); a.add_argument('--dest')
b = sp.add_parser('pull'); b.add_argument('pkg')
sp.add_parser('list')
o = ap.parse_args()
if o.cmd == 'push': push(o.name, o.dest or os.path.join(dropbox_root(), PKG_HOME_REL))
elif o.cmd == 'pull': pull(o.pkg)
else: lst()
