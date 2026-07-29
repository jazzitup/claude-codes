---
name: lecture-history-enrich
description: >
  Enrich an existing Google-Docs-paste-ready lecture note HTML (e.g. one
  produced by pennylane-codebook-notes) with fun illustrations and short
  "science history" episode boxes about real people/discoveries tied to
  each concept in the note, then save the result as a NEW HTML file in the
  same directory (never overwrite the original). Portrait photos are
  sourced from Wikipedia/Wikimedia Commons, resized, and embedded as
  base64 data URIs in the same style as the note's existing formula/diagram
  images. Use when the user has an existing lecture-note HTML and asks to
  make it "더 재밌게" / add 삽화 or 그림 / add 위인 이야기 or 발견 에피소드.
  Korean triggers: 강의노트 재밌게 만들어줘, 삽화 추가, 위인 이야기 추가,
  과학사 에피소드 넣어줘, 그림 넣어서 새 파일로 저장해줘.
---

# 강의노트 재미 보강 (역사 에피소드 + 삽화)

기존 강의노트 HTML(보통 `pennylane-codebook-notes` 스킬로 만든 것)에
개념과 연결되는 실존 인물/발견 에피소드를 짧은 "역사 박스"로 곁들이고,
그 인물의 초상 사진을 함께 넣어서 더 재미있게 만드는 스킬. 원본은 절대
건드리지 않고, 같은 디렉토리에 새 파일로 저장한다.

## 큰 그림

1. 원본 HTML을 (토큰 낭비 없이) 읽고 목차/섹션 구조를 파악한다.
2. 각 섹션의 핵심 개념과 자연스럽게 엮이는 실존 인물·발견 일화를 고른다
   (검증 가능한 사실 위주로; 전설/속설은 "전해진다" 식으로 프레이밍).
3. 그 인물의 초상 사진을 위키피디아/위키미디어 커먼즈에서 구해 리사이즈 →
   base64 인코딩 → 기존 디자인 시스템과 어울리는 새 CSS 박스에 삽입한다.
4. 결과를 원본과 다른 파일명으로 저장한다.

## 1. 원본을 토큰 낭비 없이 읽기

이런 강의노트는 수식/다이어그램이 `<img src="data:image/png;base64,...">`
로 이미 잔뜩 박혀 있어서, 파일 크기(MB 단위)에 비해 실제 텍스트 분량은
적다. 파일 전체를 `Read`로 읽으면 base64 때문에 토큰 한도를 바로
초과한다. 먼저 base64 페이로드만 잘라낸 읽기 전용 사본을 스크래치패드에
만들어서 그것으로 구조 파악을 한다.

```bash
sed -E 's#(data:image/[a-zA-Z]+;base64,)[A-Za-z0-9+/=]+#\1TRUNCATED#g' \
  "$ORIGINAL_HTML" > "$SCRATCH/original_readable.html"
```

이 사본으로 `grep -n "<h[1-4]"` 등을 이용해 목차를 뽑고, `Read`의
offset/limit으로 섹션별 본문을 읽는다. **이 사본은 읽기 전용 참고용일
뿐, 실제 편집은 항상 원본 경로(또는 그 복사본)에 대해 수행한다** — 텍스트
구간(제목/문단)은 base64를 자르지 않았으므로 원본과 완전히 동일해서,
여기서 얻은 앵커 문자열을 원본 편집에 그대로 재사용할 수 있다.

## 2. 인물/에피소드 고르기

섹션 하나당 박스 하나가 적당하다 (전부에 넣으면 산만해진다). 좋은
에피소드의 기준:
- 그 섹션의 핵심 대상(게이트 이름, 정리 이름, 시각화 도구 이름 등)에
  이름이 직접 붙어 있는 사람을 우선 고른다 (예: 파울리 X → 볼프강
  파울리, 아다마르 게이트 → 자크 아다마르, 블로흐 구 → 펠릭스 블로흐).
- 이야기에 구체적인 디테일(연도, 장소, 인용문)이 있어야 재미있다.
  두루뭉술한 "훌륭한 과학자였다" 류는 피한다.
- 잘 알려진 일화/도시전설(예: 파울리 효과)은 사실인 것처럼 단정하지
  말고 "~라는 일화가 전해진다"처럼 출처가 전설임을 드러낸다.
- 가능하면 그 섹션 뒷부분에서 배우는 다른 개념과도 은근히 연결한다
  (예: 해밀턴의 사원수 → RX/RY/RZ 회전과 대수 구조가 같다는 것).
- 검증하기 애매한 세부사실(예: 정확한 인용문 문구)은 WebSearch로 한 번
  더 확인한다.

## 3. 초상 사진 구하기

**Wikipedia REST API 요약 엔드포인트**가 제일 빠르고 안전하다 (커먼즈
`api.php`보다 rate limit이 훨씬 관대함):

```bash
curl -s "https://en.wikipedia.org/api/rest_v1/page/summary/<Title>" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
      print(d.get('thumbnail',{}).get('source')); \
      print(d.get('originalimage',{}).get('source'))"
```

`<Title>`은 URL 인코딩된 문서 제목 (`David%20Deutsch`처럼 공백은
`%20`, 괄호 있는 동명이인 문서는 `_(physicist)` 등 그대로 둔다).

라이선스가 궁금하면 커먼즈 `api.php`로 한 번 더 확인할 수 있지만
(`action=query&titles=File:...&prop=imageinfo&iiprop=url|extmetadata`),
**이 엔드포인트는 짧은 시간에 여러 번 부르면 바로 429 (Too Many
Requests)를 준다.** 여러 파일을 한꺼번에 조회하지 말고, 꼭 필요한
파일만 하나씩, 호출 사이에 몇 초 간격을 두고 조회한다. User-Agent
헤더(`-A "Mozilla/5.0 (educational lecture note project; contact
<email>)"`)를 꼭 붙인다 — 없으면 더 자주 막힌다.

이미지 자체(`upload.wikimedia.org/...`)는 CDN 정적 파일이라 이 rate
limit에 걸리지 않으니, 라이선스 확인과 별개로 바로 다운로드해도 된다.

라이선스 판단 기준:
- 사망 후 오래된 인물(19세기 이전 출생 등)의 초상화/사진은 보통
  퍼블릭도메인.
- 노벨상재단(Nobel Foundation) 크레딧 사진, 미국 정부 기관(로스앨러모스
  연구소 등 DOE) 촬영 사진도 보통 퍼블릭도메인.
- 생존 인물의 최근 사진은 CC BY / CC BY-SA인 경우가 많다 — 이 경우
  캡션이나 문서 하단 각주에 촬영자 크레딧을 반드시 남긴다.

```bash
curl -sL -A "Mozilla/5.0 (educational lecture note project; contact <email>)" \
  -o "$SCRATCH/images/<name>.orig" "<originalimage 또는 thumbnail URL>"
```

## 4. 리사이즈 + base64 인코딩

macOS에는 ImageMagick이 없는 경우가 많다 (`convert`/`magick` 없음).
내장된 `sips`로 충분하다 — 폭 200~240px, JPEG로 변환하면 인물 사진 한
장이 10~20KB 정도로 작아진다 (기존 노트의 수식 이미지들과 비슷한
용량대).

```bash
sips -Z 240 -s format jpeg -s formatOptions 78 "$name.orig" --out "$name.jpg"
base64 -i "$name.jpg" -o "$name.b64"
```

**주의**: `$name.b64`(수만 자짜리 base64 텍스트)를 `Read` 도구로 읽어서
자기 컨텍스트에 올리지 않는다 — 파이썬/bash 스크립트가 디스크에서 직접
읽어 결과 HTML에 써넣게 하면 토큰을 전혀 쓰지 않는다.

## 5. 디자인 시스템에 맞는 CSS 박스 추가

기존 노트는 CSS 커스텀 프로퍼티(`--accent`, `--exercise*`,
`--solution*`, `--note-accent` 등)를 라이트/다크 테마별로 4곳
(`:root` 기본, `@media (prefers-color-scheme: dark)`,
`:root[data-theme="dark"]`, `:root[data-theme="light"]`)에 중복
정의해 두는 패턴을 쓴다. 새 "역사 박스"도 같은 패턴을 따르되, 기존
exercise(주황)/solution(초록)/note(빨강)/accent(파랑)와 겹치지 않는
새 색(예: 보라 계열 `--hist-accent`)을 4곳 모두에 추가한다. 박스는
초상 사진(작은 썸네일, flex 레이아웃 왼쪽) + 본문(오른쪽)을 나란히
배치하고, 좁은 화면에서는 세로로 쌓이도록 미디어쿼리를 넣는다.

## 6. 앵커 기반으로 원본 파일에 삽입하기

파일이 매우 크기 때문에 `Edit` 도구로 직접 편집하는 대신, 파이썬
스크립트로 `str.replace`를 쓰되 **바꾸기 전에 항상 anchor 문자열의
등장 횟수가 정확히 1인지 확인**한다 (다르면 앵커를 더 길게 잡는다).
텍스트 구간(제목, 문단 끝)은 base64 트렁케이션과 무관하게 원본과
동일하므로, 2단계에서 만든 `original_readable.html`에서 읽은 문자열을
그대로 앵커로 재사용할 수 있다.

```python
with open(src, encoding='utf-8') as f:
    html = f.read()
assert html.count(anchor) == 1, "anchor not unique, widen it"
html = html.replace(anchor, anchor + new_box_html, 1)
```

CC BY-SA 사진처럼 크레딧이 필요하면, 문서 맨 아래 기존 각주(있다면) 옆에
사진 출처를 한 줄로 정리해 추가한다.

## 7. 저장 및 확인

- 항상 원본과 다른 파일명으로 저장한다 (예: 원본이
  `Week02_Module2_xxx.html`이면 `Week02_Module2_xxx_보강.html`처럼).
- 저장 후 `grep -c "histbox"` 등으로 박스 개수가 의도한 수만큼
  들어갔는지, `python3 -c "import re; ..."` 나 브라우저로 열어서 태그가
  안 깨졌는지 확인한다.

## 배운 것 / 반복하지 말 것

- 커먼즈 `api.php`는 몇 번만 연달아 불러도 429를 준다 — 메타데이터
  확인은 최소한으로, REST 요약 API를 우선 쓴다.
- 파일에 박혀 있는 base64 이미지 때문에 `Read` 전체 읽기는 바로 토큰
  초과로 실패한다 — `sed`로 트렁케이션한 사본을 먼저 만든다.
- base64 텍스트 자체를 모델 컨텍스트로 절대 왕복시키지 않는다 (읽지도,
  다시 쓰지도 않는다) — 항상 스크립트가 디스크 → 디스크로 옮기게 한다.
- macOS 기본 환경엔 ImageMagick이 없을 수 있다 — `sips`로 충분하다.
