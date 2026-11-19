"""추천서 hwpx 본문 칸(빈 칸 하나)에 문단들을 넣는다.
usage: python3 fill_body.py <unzipped_dir> <paras.txt> [--dean "이 름"]
paras.txt: 한 줄 = 한 문단, 빈 줄 = 빈 문단. 10pt charPr/justify paraPr는 header.xml에서 자동으로 찾는다."""
import sys, re, html, argparse
ap = argparse.ArgumentParser()
ap.add_argument('dir'); ap.add_argument('paras'); ap.add_argument('--dean')
a = ap.parse_args()
sec = f'{a.dir}/Contents/section0.xml'
x = open(sec).read(); h = open(f'{a.dir}/Contents/header.xml').read()
# 10pt(height=1000) 비굵은 글자 모양
cp = next(m.group(1) for m in re.finditer(r'<hh:charPr id="(\d+)" height="1000".*?</hh:charPr>', h, re.S)
          if '<hh:bold' not in m.group(0))
# 양쪽정렬, 160%, 들여쓰기 0 문단 모양
pp = next(m.group(1) for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', h, re.S)
          if 'horizontal="JUSTIFY"' in m.group(0) and 'value="160"' in m.group(0)
          and '<hc:intent value="0"' in m.group(0) and '<hc:left value="0"' in m.group(0))
# 가장 큰 빈 칸(텍스트 없는 문단 하나짜리 subList) = 본문 칸
cells = list(re.finditer(r'(<hp:subList [^>]*>)(<hp:p [^>]*><hp:run charPrIDRef="\d+"/>(?:<hp:linesegarray>.*?</hp:linesegarray>)?</hp:p>)(</hp:subList>.*?<hp:cellSz width="(\d+)" height="(\d+)"/>)', x, re.S))
cells = [c for c in cells if '<hp:subList' not in c.group(3)[12:]]
body = max(cells, key=lambda c: int(c.group(4)) * int(c.group(5)))
ps = ''.join(
    f'<hp:p id="0" paraPrIDRef="{pp}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
    + (f'<hp:run charPrIDRef="{cp}"><hp:t>{html.escape(l, quote=False)}</hp:t></hp:run>' if l else f'<hp:run charPrIDRef="{cp}"/>')
    + '</hp:p>' for l in open(a.paras).read().rstrip('\n').split('\n'))
x = x[:body.start(2)] + ps + x[body.end(2):]
if a.dean:
    m = re.search(r'대학장 :\s+\(인\)', x); assert m, '대학장 칸 없음'
    x = x[:m.start()] + f'대학장 :    {a.dean}     (인)' + x[m.end():]
open(sec, 'w').write(x)
w = int(body.group(4)) - 1020; hgt = int(body.group(5)) - 282
print(f'charPr={cp} paraPr={pp} body cell {body.group(4)}x{body.group(5)} → ~{hgt//1600} lines x ~{w//1000} 한글자')
