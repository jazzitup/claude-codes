---
name: emeritus-recommendation
description: 명예교수 추대 서류(개별조서·교육및학술상의업적조서·공적조서 .hwp, 학술상의업적 별지 .hwpx)를 읽고 '추천서' hwpx 양식의 본문 칸에 추천서를 써 넣는다. 한 페이지를 절대 넘기지 않고 글자 크기 10pt. .hwp는 olefile로 텍스트만 읽는다(편집 안 함). '명예교수 추천서 써줘', '이 서류들 읽고 추천서 작성', '추천서 hwpx에 써줘' 요청 시 사용. 다른 추천서 양식(표 안 큰 본문 칸 + 하단 날짜/서명)에도 그대로 쓸 수 있다.
---

# 명예교수 추천서 작성 (hwp 서류 읽기 → 추천서 hwpx 채우기)

학과장이 퇴직 교원의 명예교수 추대 서류 묶음을 받아 마지막 '추천서'를 쓰는 일.
보통 Google Drive의 학과장 업무 폴더 안 `<교수명> 명예교수 추천/추천서류양식 .../`에
`1. 개별조서*.hwp`, `2. 교육및학술상의업적조서*.hwp`, `3. 공적조서*.hwp`,
`4. 추천서*.hwp(x)`, `학술상의업적_별지*.hwpx`가 있다. (실제 경로·이름은 사용자가 준다.
이 공개 repo에 개인 이름·주소를 적지 말 것.)

## 0. 준비 (컴퓨터마다 한 번)

```bash
python3 -m venv ~/.venvs/research 2>/dev/null; ~/.venvs/research/bin/pip install -q olefile
```
- Google Drive for desktop 설치·로그인(경로 `~/Library/CloudStorage/GoogleDrive-<계정>/My Drive/...`).
  파일이 "온라인 전용"이면 Finder에서 열어 내려받게 하거나 `cat`으로 한 번 읽으면 받아진다.
- 페이지 확인용 Hancom Office HWP(맥 앱). 없으면 사용자가 직접 열어 확인.
- [[hwpxskill]]의 `scripts/validate.py`, `text_extract.py` 사용.

## 1. 서류 읽기

```bash
SK=~/.claude/skills/emeritus-recommendation/scripts
for f in "$D"/*.hwp; do echo "== $f"; ~/.venvs/research/bin/python $SK/hwp2txt.py "$f"; done
python3 ~/.claude/skills/hwpxskill/scripts/text_extract.py "$D/학술상의업적_별지*.hwpx"
```
- `text_extract.py`는 표 안 글을 빠뜨린다 → 별지의 연구비·대외활동 표는 unzip 후
  `Contents/section0.xml`의 `<hp:t>`를 문단별로 이어 붙여 읽는다.
- 추천서 `.hwp`만 있고 `.hwpx`가 없으면 사용자에게 한글에서 hwpx로 다시 저장해 달라고 한다.

## 2. 추천서 문장 (존댓말 "~합니다" 체)

5문단 정도, 문단 사이 빈 줄:
1. 추천 취지 — 부임 연월, 정년 연월, 재직 년수, "…명예교수로 추천합니다."
2. 교육 — 교수법, 대학원생 지도
3. 연구 — 논문 수·대표 논문(학술지·연도·의의), 국책과제 건수·총액(별지 표 합산), 학술발표 건수, 심사위원, 수상, 역서
4. 행정·봉사 — 주요 보직(개별조서 순서대로), 학회·정부기관 위원
5. 맺음 — "…추대하고자 이에 적극 추천합니다."

서류끼리 숫자가 다르면(예: 조서 "SCI 60편" vs 별지 "총 70편") 하나를 고르고 보고 때 짚는다.

## 3. 한 페이지·10pt 지키기

- 본문 칸은 고정 크기 표 칸이다. 넘치면 칸이 늘어나 2쪽이 된다.
- `fill_body.py`가 칸 크기로 대략 줄 수(10pt 160% → 한 줄 1600 HWPUNIT)와 줄당 글자 수를 알려준다.
  (이번 양식: ~24줄 × ~49자.) 문단별 `ceil(폭/줄폭)` 합이 **줄 수 - 1 이하**가 되게 다듬는다
  (한글 1000, 영문·숫자·공백 ~520 단위로 계산).

```bash
W=<scratchpad>/rec; rm -rf $W; mkdir -p $W/u; cd $W/u && unzip -q "<추천서.hwpx>"
cp "<추천서.hwpx>" $W/orig_backup.hwpx            # 원본 백업
python3 $SK/fill_body.py $W/u $W/paras.txt --dean "<대학장 이름>"   # 다른 서류에 적힌 이름
cd $W/u && zip -q -X -0 ../out.hwpx mimetype && zip -q -X -r ../out.hwpx . -x mimetype
python3 ~/.claude/skills/hwpxskill/scripts/validate.py ../out.hwpx
```

## 4. 페이지 수 확인 (필수)

`out.hwpx`를 `~/Documents/`에 복사해 `open -a "Hancom Office HWP"`로 열고
`screencapture -x`로 화면을 찍어 **상태표시줄의 "1/1쪽"**을 확인한다. 2쪽이면 문장을
줄여 3절 반복. 확인 뒤 Cmd+W로 닫고 테스트 파일 삭제, `out.hwpx`를 원래 추천서 경로에 덮어쓴다.
(PDF가 필요하면 [[overtime-log]] 4절 방식. 다중 모니터면 좌표 클릭이 어긋날 수 있다.)

## 5. 보고

문단별 요약, 1쪽·10pt 확인 결과, 채운 대학장 이름/비워 둔 날짜, 서류 간 불일치, 백업 경로.
