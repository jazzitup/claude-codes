---
name: evernote-reference-organize
description: >
  Evernote에 저장된 논문 노트에서, 본문(주로 introduction)에 번호로 인용된
  레퍼런스 구간(예: "...16,17, ...18, ...23–25...")을 그 논문의 References
  섹션과 대조해서 제목/저자/링크를 채운 뒤, 방법론(주제)별로 묶어서 노트 안의
  지정된 섹션(예: 노란색 "Notes" 헤딩) 밑에 예쁘게 정리해 넣는다. 사용자가
  "Evernote 노트에 있는 논문 레퍼런스 정리해줘" / "N번부터 M번 레퍼런스
  정리해서 Notes 밑에 넣어줘"라고 할 때 사용한다.
---

# Evernote 논문 레퍼런스 정리하기

2026-10-14에 "Emergent geometry and duality in the carbon nucleus"
(Nature Commun. 14, 2777 (2023)) 노트에서, intro의 "¹²C 구조 연구 방법론"
문단에 나열된 ref. 16–34를 방법론별로 정리해서 노란색 "Notes" 섹션 밑에
넣으면서 확립한 과정.

## 0. 입력 파악

사용자가 주는 것은 보통 다음 두 가지다:
- `evernote:///view/<userId>/<shard>/<noteGuid>/<noteGuid 또는 notebookGuid>` 형태의 로컬 링크.
  **세 번째 경로 세그먼트가 노트 GUID**다 (`get_note`에 바로 넣으면 된다).
- 본문에서 복사-붙여넣기한 텍스트 조각 (예: "the no-core shell model16,17,
  ..."). 이 안의 작은 위첨자 숫자들이 그대로 텍스트로 붙어 나온다 — 이게
  **그 논문의 실제 레퍼런스 번호**이므로 믿고 그대로 쓴다(사람이 직접
  PDF에서 복사했으므로 OCR 오류 걱정 없음).

## 1. 노트 열어서 구조 파악 + 논문 PDF 찾기

`get_note(noteId)`로 본문(ENML)과 `resources`(첨부파일 목록: id, hash, mime,
name)를 확인한다. 보통 본문 자체에 Abstract만 있고, 실제 논문 PDF는
`<en-media hash="..." type="application/pdf" />`로 첨부되어 있다(원논문 +
Supplementary Information 두 개가 같이 붙어있는 경우가 많다 — 파일명으로
구분: `...pdf` vs `..._SM.pdf`).

노트 안에 "Notes", "References" 같은 섹션 헤딩이 이미 색깔별로 구분되어
있을 수 있다(`<span style="color:rgb(229, 158, 37);">`처럼 — 이 RGB 값이
"노란색/주황색" 헤딩이다). 사용자가 "노란색 Notes 밑에" 라고 지정하면,
`get_note` 결과에서 정확히 그 헤딩의 전체 태그(색상 style 포함)를 찾아서
다음 단계의 `replace` anchor로 쓴다.

## 2. 논문 PDF 다운로드해서 References 섹션 읽기

```
get_attachment(noteId, hash)  # hash는 <en-media hash="..."> 값
```
결과의 `downloadUrl`은 **5분 정도면 만료**되는 서명 URL이므로, 받자마자
바로 `curl`로 스크래치패드에 내려받는다:
```bash
curl -s -o "$SCRATCH/paper.pdf" "<downloadUrl>"
```
`pdfinfo paper.pdf | grep -i pages`로 전체 페이지 수를 확인하고, 보통 짧은
논문(Nature Commun. 등)은 **References가 본문 뒤쪽 1~2페이지**에 있으므로
마지막 1~2페이지를 `Read(file_path, pages="N-1-N")`로 이미지로 읽는다 —
References는 번호가 매겨진 목록이라 이미지로 바로 읽어도 제목/저자/저널/
권/페이지/연도를 정확히 옮길 수 있다.

**본문의 위첨자 인용 번호가 애매하면(예: 같은 숫자가 서로 다른 항목에
반복돼서 오타처럼 보일 때)** `pdftoppm -png -r 400`으로 해당 페이지를
고해상도로 뽑고, Python PIL로 그 문단 부분만 crop + 2배 확대해서 다시
`Read`로 확인한다 — 400dpi 이상에서 보면 작은 위첨자 숫자도 명확히
구분된다. 실제로 겹치는 것처럼 보여도 원문이 정말 그렇게 쓰여 있을 수
있다(예: 이번 논문에서 FMD와 ACM이 똑같이 ref. 26을 공유 — 오타가
아니라 저자들이 실제로 그렇게 썼다. 이런 경우 "원문 그대로"라고
명시하고 넘어간다. 멋대로 번호를 고치지 않는다).

## 3. 인용 구간을 "방법론별 번호 그룹"으로 매핑

사용자가 준 pasted 텍스트(또는 본문에서 찾은 해당 문장)를 그대로
파싱한다. 예:
```
the no-core shell model16,17, symmetry-adapted no-core shell model18,
shell model19, ..., antisymmetrized molecular dynamics (AMD)23–25, ...
```
→ 각 방법론 이름을 키(key)로, 그 뒤에 붙은 번호(쉼표로 나열되거나
`23–25`처럼 범위로 묶인 것 모두 전개)를 값으로 하는 그룹을 만든다. 번호
범위(`23–25`)는 23,24,25 전부를 그 그룹에 넣는다.

## 4. 각 레퍼런스 번호의 정확한 DOI/링크를 웹 검색으로 확인한다 — 절대 URL을 지어내지 않는다

2단계에서 읽은 References 목록에는 제목·저자·저널·권·페이지·연도는 있지만
링크(DOI)는 보통 없다. **URL을 추측해서 쓰지 않는다** — APS(Phys. Rev.
계열)처럼 DOI 패턴이 결정론적(`10.1103/PhysRev<X>.<vol>.<page>`)이어도,
`WebSearch`로 그 논문 제목+저자+저널 정보를 검색해서 실제로 DOI나
arXiv 링크가 검색 결과에 나오는지 확인한다.

- 검색 결과에 `link.aps.org/doi/10.1103/...` 또는 `doi.org/10.1103/...`
  같은 링크가 직접 나오면 그 DOI를 채택한다.
- 저널 DOI가 검색으로 안 나오고 arXiv 프리프린트만 확인되면(2026-10-14
  세션에서 3개 항목이 이 경우였다 — 비APS/비Springer 저널 DOI는 검색
  엔진이 잘 안 잡아줌), **arXiv 링크를 쓰고 "저널판 DOI는 확인 못함"이라고
  명시**한다. 지어낸 DOI를 적지 않는다.
- 레퍼런스 개수가 많으면(10개 이상) `WebSearch` 호출을 한 메시지에
  병렬로 여러 개 보내서 왕복 횟수를 줄인다.

## 5. ENML로 정리해서 노트에 삽입

사용자가 예시로 준 형식을 그대로 따른다:
```
* 방법론 이름
   * [번호] 제목, 저자, 논문 링크
   * [번호] 제목, 저자, 논문 링크
```
ENML 중첩 리스트로 구현: `<ul><li><strong>방법론</strong><ul><li>[16] "제목"
— 저자 — 저널 권, 페이지 (연도) — <a href="https://doi.org/...">link</a>
</li></ul></li></ul>`.

- 저자가 4명을 넘으면 첫 저자만 쓰고 `et al.`을 붙인다(`Navrátil, P. et al.`).
  3명 이하면 전부 쓴다(`Zhao, P. W., Itagaki, N. & Meng, J.`).
- 제목 안의 `"`, `&`는 ENML 엔티티(`&quot;`, `&amp;`)로, 위첨자 숫자(¹²C
  등)는 `&sup1;&sup2;C`처럼 HTML 엔티티로 이스케이프한다. 원문에 있는
  é, ß, ö 같은 비ASCII 문자는 그대로 UTF-8로 써도 된다(이스케이프 불필요).
- `edit_note(mode="replace")`로 삽입한다. `find`는 `get_note`에서 읽은
  타겟 헤딩의 **정확한 전체 태그**(색상 style, `--en-nodeId` 포함)와 그
  바로 뒤에 있던 빈 `<div><br/></div>` 블록까지 포함해서 고유하게 만든다
  — 헤딩만 넣으면 문서 안에서 유일하지 않을 수 있다. `content`에는 같은
  헤딩을 그대로 복사해 넣고 바로 뒤에 새 리스트를 붙여서, 헤딩 자체는
  지우지 않고 그 "밑에" 들어가게 만든다.

## 알아둘 것

- 첨부 PDF의 `get_attachment` 다운로드 URL은 금방 만료되므로, 받자마자
  바로 `curl`로 내려받는다 — 다른 작업을 먼저 하다가 나중에 받으면
  403/만료 에러가 난다.
- 논문 원문 자체의 레퍼런스 번호 중복/오류처럼 보이는 것도, 실제로 저자가
  그렇게 쓴 것이면 "정리자가 고친 것"처럼 보이지 않게 원문 그대로 반영하고
  그 사실을 한 줄 남긴다(예: "ACM도 FMD와 동일하게 ref. 26으로 표기되어
  있음 — 원문 그대로").
- 이 스킬은 **정리만** 한다 — 레퍼런스 논문 자체의 PDF를 새로 다운로드해서
  노트에 다시 첨부하거나 하지 않는다(이미 있는 PDF를 참고용으로만 읽는다).
