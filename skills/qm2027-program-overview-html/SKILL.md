---
name: qm2027-program-overview-html
description: "QM2027 'POC's parallel selection' Google Sheet(17개 트랙 탭: CH, CD, EM, FA, EI, LC, AQ, HF, IS, JE, LF, NT, AS, UP, CP, SM, EX)의 각 트랙별 Primary list(90%)/Secondary candidate 선정 결과를, 트랙마다 하나의 섹션(program)으로 묶은 HTML 페이지로 만든다. 각 섹션의 테이블은 Rank/Id/Category/Collaboration만 보여주는 압축된 형태이고, Primary는 분홍, Secondary는 파랑 배경으로 행을 구분한다. 각 행에 'abstract ▾' 토글 버튼이 있어 누르면 그 밑에 Title/Authors/Presenter/Score/Leading Talk/LOC Confirm/Merge suggestion/Comment(POC가 남긴 모든 코멘트)와 QM2027_abstracts PDF에서 가져온 전체 abstract 본문이 펼쳐진다. '프로그램별로 html 저장해줘', 'Rank Id Category Collaboration 표로 만들어줘', '토글 버튼으로 전체 abstract 보여줘', 'POC 코멘트까지 다 보이게' 요청 시 사용. 시트에 트랙이 새로 채워지거나 abstract PDF가 갱신되면 처음부터 다시 돈다."
---

# QM2027 트랙별 Program Overview HTML

## 0. 언제 쓰나

"POC's parallel selection" Google Sheet의 트랙 탭들(위 description의 17개 탭)에 입력된
Primary/Secondary 선정 결과를 사람이 훑어보기 좋은 HTML 한 페이지로 만들어 달라는
요청에 쓴다. [[qm2027-selection-stats]]가 "숫자 통계"를 뽑는 스킬이라면, 이 스킬은
"선정 리스트 자체를 보기 좋게 보여주는 페이지"를 만든다 — 서로 보완 관계.

핵심 요구사항(사용자가 명시한 디자인):
- 트랙(program) 하나당 섹션 하나.
- 테이블 컬럼은 **Rank, Id, Category, Collaboration만** — Title은 테이블에 안 보인다.
- Primary 행과 Secondary 행을 **배경색으로 구분**.
- 각 행에 버튼이 있어 누르면(토글) 그 발표의 **전체 abstract**가 펼쳐진다. 전체
  abstract에는 Title/본문뿐 아니라 **Merge 제안, POC가 남긴 Comment 등 시트에 적힌
  모든 코멘트도 함께** 보여준다 — abstract 본문만 보여주면 안 된다.

## 1. Google Sheet에서 트랙별 데이터 뽑기 (브라우저)

각 트랙 탭은 보통 이런 구조다 (탭마다 약간씩 다를 수 있음 — 2절 참고):

```
Row1: POC Liaison: <이름들>
Row2: IAC POC members: <이름들>
Row4: Oral — Primary list (90% target: N talks)   [탭마다 문구 다름, 아래 참고]
Row5: Rank  Id  Title  Affiliation  Category  Collaboration  Score  Merge with  Comment  Leading Talk 여부  ...  LOC Confirm
Row6..: <Primary 데이터 행들, 배경 분홍/빨강>
(빈 행)
Row N: Oral — Secondary candidates (ranked — compete in 2nd-round ...)
Row N+1: (헤더 재등장)
Row N+2..: <Secondary 데이터 행들, 배경 하늘색>
```

**변형들** (파서가 이미 대응함, `scripts/build_data.py` 참고):
- LC처럼 "(90% target: N talks)" 대신 "(POC-designated "Strong recommended", N talks)"
  같은 자유 문구를 쓰는 탭도 있다 — 파서는 `Oral — ...` 로 시작하는 줄이면 전부 섹션
  경계로 인식하고, 그 줄에 "secondary"라는 단어가 있는지만으로 Primary/Secondary를
  가른다.
- UP처럼 Primary/Secondary 구분 없이 "Oral — (10 talks, POC-...)" 한 블록만 있는
  탭도 있다 — 이 경우 전부 `primary`로 처리된다 (대신 Rank 칸에 "TOP" 같은 특수
  표시가 있을 수 있음).
- Category 값은 탭마다 "Theory"/"Experiment" 풀네임이거나 "th"/"exp" 축약형일 수
  있다 — 파서가 둘 다 정규화한다.
- 아직 채워지지 않은 탭(헤더만 있고 데이터 행이 0개)도 있을 수 있다 — 그런 트랙은
  "아직 선정 결과가 입력되지 않았습니다" 안내만 넣고 테이블은 생략한다.

### 1-1. 브라우저로 탭마다 복사하기

Google Sheets는 셀 배경색을 안정적으로 긁어오기 번거로우므로(각주 참고), **색 대신
Primary/Secondary 섹션 라벨 텍스트로 구분**하는 게 훨씬 안정적이다. 그래서 각 탭의
A1:N60 (또는 더 넓게, SM처럼 컬럼이 많은 탭은 A1:Z80) 범위를 선택해 복사하면 TSV
텍스트 안에 그 라벨 줄이 그대로 들어있어 충분하다.

절차 (탭마다 반복):
1. 시트 탭을 클릭해서 전환한다. **주의**: Google Sheets 탭바는 활성 탭이 굵게
   표시되면서 폭이 바뀌어 옆 탭들의 x좌표가 매번 밀린다. 좌표를 한 번 구해서
   재사용하지 말고, **클릭 직전에 `zoom`으로 탭바 영역(예: region [700,925,1100,950])을
   다시 찍어 각 탭 라벨의 실제 중심 좌표를 구한 뒤 바로 클릭**한다. 클릭 후에는
   `document.querySelector('.docs-sheet-active-tab .docs-sheet-tab-name').textContent`
   로 실제로 전환됐는지 JS로 확인하고, 안 됐으면(가끔 드롭다운 화살표를 눌러
   컨텍스트 메뉴가 뜬다 — Escape로 닫고 재시도) 다시 클릭한다. Name Box나 URL의
   gid 값도 바뀌었는지 보조로 확인할 것.
2. Name Box에 `A1:N60`(또는 `A1:Z80`) 입력 후 Enter로 범위 선택.
   - "Invalid range — The range you specified exceeds the sheet size" 에러가 뜨면
     그 탭의 실제 그리드가 더 작다는 뜻이니 OK로 닫고 더 좁은 범위(`A1:N50` 등)로
     재시도한다. 이 에러창은 모달이라 떠 있는 동안 탭 전환 클릭이 전부 씹힌다.
3. `Cmd+C`로 복사.
4. `javascript_tool`로 `await navigator.clipboard.readText()` 읽어서
   `window.__sheetData[탭코드] = text` 에 누적 저장. 17개 탭 다 돈 다음 한꺼번에
   꺼낸다(아래).

### 1-2. 데이터 꺼내기

`window.__sheetData`는 탭마다 수 KB~십수 KB라 전체 합치면 수십~백KB대다. 채팅
응답으로 직접 꺼내지 말고, PDF 다운로드 때 쓰던 패턴처럼 Blob+`<a download>`로
`qm2027_track_sheets.json`을 다운로드한 뒤, `~/Downloads`는 Bash 샌드박스로 직접
목록 조회가 안 될 수 있으니 `mdfind -onlyin ~/Downloads "kMDItemFSName == '파일명'"`
으로 경로를 찾아서 `cp`로 스크래치패드/작업 디렉터리로 옮긴다.

**다 받은 뒤 반드시 무결성 체크**: 각 탭 데이터의 첫 줄(`POC Liaison: ...`)이 서로
다 다른지 확인한다. 같은 내용이 두 탭에 중복돼 있으면 탭 전환이 실제로 되기 전에
복사가 실행된 것이므로(레이스 컨디션), 그 탭들을 다시 받는다.

## 2. Indico abstract book PDF에서 전체 abstract 가져오기

[[qm2027-selection-stats]] 2절과 같은 PDF(`/Users/yongsunkim/My Gdrive/개인서류
drive/QM2027/QM2027_abstracts_all_<날짜>.pdf`, 없거나 오래됐으면 새로 받기)를 쓰되,
이번엔 Category/Collaboration뿐 아니라 **Title과 본문(Content) 전체**가 필요하다.

```bash
pdftotext -layout QM2027_abstracts_all_<날짜>.pdf all.txt
python3 scripts/parse_full.py all.txt full_abstracts.json
```

`full_abstracts.json`은 abstract ID별로 title/body/category/collab/authors/
presenter/track/type/status를 담는다. 페이지 넘김 때 생기는 머리글/쪽번호 노이즈는
스크립트 안 `clean_footer()`가 제거한다.

## 3. 시트 데이터 + PDF 데이터 합치기

```bash
python3 scripts/build_data.py qm2027_track_sheets.json full_abstracts.json tracks_full.json
```

이 스크립트는:
- 탭별 TSV를 Rank/Id/Title/Affiliation/Category/Collaboration/Score/Merge with/
  Comment/Leading Talk/LOC Confirm 컬럼으로 파싱하고(헤더 행에서 컬럼명 →
  인덱스 매핑을 매번 새로 만들기 때문에 탭마다 컬럼 순서/개수가 달라도 안전함),
  "Oral — ..." 라벨 줄로 Primary/Secondary 섹션을 가른다.
- 각 항목의 Id로 `full_abstracts.json`을 조회해 title/body/authors/presenter/
  category_pdf를 채운다(시트의 Title/Category는 요약용 사본일 뿐이라 종종 짧게
  잘려 있거나 오타가 있을 수 있어, 토글에 보여줄 "진짜" 본문은 항상 PDF 쪽을
  우선한다).
- 끝에 `missing abstract lookups`가 출력되면 시트의 Id가 PDF에 없다는 뜻이니
  (오탈자 등) 사람이 확인해야 한다 — 조용히 넘어가지 않는다.

## 4. HTML 생성

```bash
python3 scripts/build_html.py tracks_full.json qm2027_program_overview.html
```

- 외부 의존성 없음(표준 라이브러리만). 라이트/다크 모드 모두 대응(`prefers-color-scheme`).
- 트랙마다 `<section>`, 그 안에 Rank/Id/Category/Collaboration 4컬럼 테이블.
  Primary 행은 분홍 배경, Secondary는 하늘색 배경(`--primary-bg`/`--secondary-bg`
  CSS 변수로 라이트/다크 둘 다 정의돼 있음). Category는 추가로 작은 컬러 뱃지로도
  표시(Theory=보라, Experiment=청록) — 행 배경(Primary/Secondary)과 헷갈리지
  않도록 일부러 다른 축으로 구분했다.
- 각 행 바로 아래 숨겨진 `<tr class="detail-row">`가 있고, 같은 행의
  "abstract ▾" 버튼이 순수 JS `toggleDetail(id)`로 그 행의 `open` 클래스를
  토글한다(프레임워크 없음, 페이지 혼자 완결).
- 토글 내용에는 abstract 본문뿐 아니라 **Presenter, Authors, Affiliation(시트
  기재분), Score, Leading Talk 여부, LOC Confirm, Merge suggestion, Comment
  (POC가 남긴 코멘트)까지 전부** 넣는다 — "abstract만" 보여주면 안 된다는 게
  사용자의 명시적 요구사항이었다.
- 상단에 트랙 코드+이름+건수로 된 목차(anchor 링크)를 자동 생성한다.
- 아직 데이터가 없는 트랙(헤더만 있고 Primary/Secondary 행이 0개)은 테이블 대신
  "아직 선정 결과가 입력되지 않았습니다 (POC Liaison: ...)" 안내만 넣는다 — 조용히
  빼먹지 않고 전체 17개 트랙을 다 보여준다.

## 5. 저장 위치

사용자가 별도 경로를 안 주면 `/Users/yongsunkim/My Gdrive/개인서류 drive/QM2027/`에
저장한다(이 세션에서 이 폴더가 기본 산출물 위치로 반복 지정됨). 과거 버전을 덮어쓸지
새 파일명으로 할지는 애매하면 사용자에게 확인 — 이 페이지는 선정 작업이 진행되면서
계속 갱신될 성격의 "현재 상태 스냅샷"이라 보통 같은 파일명을 덮어써도 되지만,
중요한 마일스톤(예: 1차 마감 직후)에는 날짜를 붙인 사본을 남기는 것도 고려할 것.

## 6. 재실행 시 유의

- 시트에 새 트랙이 채워지거나 기존 선정이 바뀌면 1절부터 다시 돈다 — 중간 JSON을
  재사용하지 말 것(특히 abstract PDF가 갱신됐으면 2절도 다시).
- 시트 탭 전환이 레이스 컨디션에 취약하다는 걸 1-1절에서 거듭 강조한 이유: 이전
  세션에서 실제로 탭 전환이 완료되기 전에 복사를 실행해 다른 탭의 데이터가
  섞여 들어간 적이 있었다(JE를 캡처했다고 생각했는데 실제로는 IS 데이터였음).
  탭마다 반드시 "전환 확인 → 복사"의 순서를 지키고, 끝나고 나서 1-2절의 무결성
  체크(POC Liaison 줄이 탭마다 다 다른지)를 생략하지 말 것.
