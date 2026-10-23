---
name: evernote-paper-library
description: "Claude가 리서치/토론 중에 추천·논의한 논문(대화 맥락에서 나온 여러 편) 또는 사용자가 준 논문 링크를 Evernote 논문 라이브러리에 정리한다. 논문마다 '04. Library' 스택 안에서 주제에 가장 알맞은 노트북을 골라 노트를 만들고, paper 링크/title/authors/abstract(전부 원문 그대로)와 Claude 자신의 설명(왜 관련 있는지)을 적고 PDF를 첨부한다(가능하면 저널판, 안 되면 arXiv판). 그 다음 'La Bibliothèque de Babel' 목차 노트의 맨 위 'Reading..' 목록 맨 위에 새 논문 링크를 넣는다 — 새 논문은 주제 섹션(A~J)이 아니라 항상 Reading..에만 넣는다. Reading..에서 다 읽은(체크된) 논문은 그 아래의 어울리는 주제 섹션으로 옮긴다. [[evernote-paper-to-read]]와 다른 점: 그 스킬은 링크 1개를 '[T] To read' 노트북에 4필드로 저장하는 단순 케이스이고, 이 스킬은 '설명' 필드까지 포함해서 주제별 노트북에 저장하고 Babel의 Reading.. 목록까지 갱신하는 확장 케이스다(1편이든 여러 편이든 이 스킬 사용). '이 논문 라이브러리에 저장해줘', '이 논문들 에버노트에 넣어', '논문 evernote에 정리해줘', 'Reading 리스트 업데이트해', '읽은 논문 정리해줘/옮겨줘' 요청 시 사용."
---

# Evernote 논문 라이브러리 정리 (paper note + Reading.. 목록 + 읽은 논문 이동)

## 0. 배경

사용자는 물리학 논문을 Evernote에 노트 한 편씩 정리해 둔다.

- **노트가 들어가는 곳:** 노트북 스택 **"04. Library"** 아래의 주제별
  노트북들(예: `[C] EIC, UPC, LHC, RHICf`, `[Q] QC, entanglement, ML`,
  `[N] nucl-th and nucl-ex`, `[H] hadrons`, `[L] lattice`, `[G] GR and
  cosmology`, `[M] ePIC detector`, `[A] LAMPS, ...`, `[B] P_c, ...` 등).
  노트북 구성은 바뀔 수 있으니 매번 `search_notebooks`로 다시 확인한다.
- **목차 노트:** 같은 스택의 `[0] Library index` 노트북에 있는
  **"La Bibliothèque de Babel"** 노트. 맨 위에 **"Reading.."** 목록이
  있고, 그 아래에 주제 섹션(`A. [Library] nucl-th & nucl-ex`, `C. [Library
  C] EIC, UPC, LHC, RHICf`, `D. [Library] QC, entanglement, Quantum info`,
  `G. [Library] QCD` 등, `A`~`J` 정도)이 있다.
- **흐름:** 새 논문 → 노트 생성 → **Reading..에만** 링크. 사용자가 읽고
  체크하면 → 그 항목을 어울리는 주제 섹션으로 **옮긴다**.
  예: Reading..의 `Notes on mixed state and pure state and entanglement`가
  체크되면 → `D. [Library] QC, entanglement, Quantum info`로 이동.
- **형식 예시 노트:** 사용자가 지정한 표준 예시는
  `Hatta, Schoenleber (2025) Probing quantum entanglement with generalized
  parton distributions at the Electron-Ion Collider` 노트다
  (`intitle:"Hatta, Schoenleber"`로 찾는다). 새 노트는 이 노트의 ENML을
  그대로 본뜬다.

## 0.1 핵심 원칙

- **서식을 손으로 재현하지 않는다.** 예시 노트를 `get_note`로 읽어서 그
  ENML(라벨, 폰트, 링크 구성)을 그대로 본떠 쓴다.
- **title/authors/abstract는 원문 그대로.** arXiv API/INSPIRE-HEP
  메타데이터의 원문을 의역·요약하지 않는다. abstract에 MathML
  (`<math>...</math>`)이 섞여 나오면(특히 INSPIRE API) ENML이 깨지므로
  유니코드 텍스트로 치환한다. 모든 텍스트는 XML 이스케이프(`&`→`&amp;`,
  `<`→`&lt;`)한다.
- **"설명"은 Claude가 실제로 한 말이다.** 대화에서 그 논문을 왜
  추천했는지 실제로 설명한 내용을 적는다 — 지어내지 않는다.
- **사용자가 도중에 일부 논문을 빼라고 하면** 이미 만든 노트는
  `delete_note`(휴지통 이동, 복구 가능)로 정리하고 Reading..에도 넣지
  않는다.
- **이 SKILL.md(공개 git repo)에는 실제 notebookId·noteId·계정
  번호(`<account>/<shard>`)를 적지 않는다.** 실제 값은 실행 시점에
  `search_notebooks`/`search_notes`/`get_note`로 읽어온다. 노트북·노트를
  가리킬 때는 이름/제목으로만 적는다.
- **Babel 노트는 사용자가 실시간으로 편집한다.** `edit_note(mode:
  "replace")`의 `find`가 매치 안 되면 Babel 노트를 다시 `get_note`로 읽어
  최신 상태 기준으로 앵커를 다시 뽑는다. Babel 노트는 매우 커서(16만자+)
  `get_note` 결과가 파일로 저장되므로, python으로 필요한 구간만 잘라
  읽는다.

## 1. Evernote MCP 연결 확인

`mcp__evernote__*` 도구가 없으면 사용자에게 알리고 멈춘다
([[evernote-weekly-todo]] 10절 참고 — `claude mcp add -s user ...` +
Terminal.app에서 `claude mcp login evernote` 후 세션 재시작).

## 2. 노트북 고르기 ("04. Library" 스택 안)

1. `search_notebooks({query:"", maxResults:100})`로 전체 노트북을 받고
   `stack == "04. Library"`인 것만 추린다.
2. 논문 주제에 가장 알맞은 노트북을 고른다(노트북 이름이 주제다).
   예: small-x/포화/EIC/UPC → `[C] EIC, UPC, LHC, RHICf`; 얽힘/양자정보 →
   `[Q] QC, entanglement, ML`; 핵구조·핵력 → `[N] nucl-th and nucl-ex`.
   `[0] Library index`(목차 전용)와 `[T] To read`
   ([[evernote-paper-to-read]] 전용)에는 넣지 않는다.
3. 애매하면(두 노트북에 걸치는 주제 등) 사용자에게 한 줄로 확인한다.

## 3. 형식 예시 노트 읽기

0절의 예시 노트를 `get_note`로 읽어 확인한다:
- 맨 앞 `<div><br/></div><en-media hash="..." type="application/pdf"
  style="--en-viewAs:attachment;" /><div><br/></div>`
- `paper` / `title` / `authors` / `abstract` / `설명` / `further reads`
  각 라벨: `<h1><span style="font-family: &quot;Fira Code&quot;, Consolas,
  ... monospace;"><span style="font-size: 25px;">라벨</span></span></h1>`
  (예시 노트의 정확한 문자열을 복사한다. `--en-nodeId` 스타일 값은 새
  노트에 넣지 않는다.)

## 4. 논문마다 노트 만들기

1. **메타데이터:** arXiv API(`http://export.arxiv.org/api/query?id_list=
   <ID1>,<ID2>,...` — 여러 편을 한 번에)에서 title/authors/abstract/연도를
   원문 그대로 가져오고, INSPIRE(`https://inspirehep.net/api/arxiv/<ID>?
   fields=dois,publication_info`)에서 DOI와 학술지 정보를 가져온다.
   대형 협업 논문은 저자 대신 `"<실험명> Collaboration"`으로 적는다.
2. **노트 제목:** `"<저자> (<arXiv 연도>) <논문 제목>"` — 저자 1~3명이면
   성만 나열(`Iancu, Venugopalan`), 4명 이상이면 `<제1저자 성> et al.`.
3. `create_note({title, notebookId})` (2단계에서 고른 노트북). 여러
   편이면 한 번에 병렬로 만든다.
4. **PDF 받기 — 저널판 우선, 안 되면 arXiv판:**
   - DOI로 출판사 PDF를 먼저 시도한다(오픈 액세스 학술지: MDPI
     `https://www.mdpi.com/<...>/pdf`, Springer `https://link.springer.com/
     content/pdf/<DOI>.pdf`, IOP `.../article/<DOI>/pdf`, Annual Reviews
     `.../doi/pdf/<DOI>` 등). 브라우저 User-Agent를 붙여 `curl -sL`.
   - 받은 파일은 반드시 `file <파일>`로 진짜 PDF인지 확인한다. 출판사
     대부분이 봇 차단으로 HTML을 돌려주므로(2026-10 기준 Elsevier,
     Springer, MDPI, IOP, Annual Reviews 모두 실패) 그러면 바로
     `https://arxiv.org/pdf/<ID>`로 대체한다.
   - 어느 판을 첨부했는지 `paper` 섹션에 적는다(예: `(첨부 PDF는
     arXiv판)`).
5. **PDF 첨부 (3단계 API):**
   1. `md5 -q <파일>`(소문자 hex), `stat -f%z <파일>`.
   2. `start_attachment_upload({noteId, hash, sizeBytes})`.
      `alreadyUploaded:true`면 업로드 생략(같은 PDF가 계정에 이미 있는
      경우). 아니면 **받은 지 1시간 안에** 업로드한다 — `uploadUrl`은
      `X-Goog-Expires=3600`이라 오래 두면 POST가 HTTP 400으로 거부되고
      세션 URL이 비어 나온다. 그러면 `start_attachment_upload`를 다시
      호출해 새 URL을 받는다.
      - `POST <uploadUrl>` 헤더 `x-goog-resumable: start`,
        `x-upload-content-length: <size>`, `content-length: 0` → 응답
        `Location:` 헤더가 세션 URL(비어 있으면 위 만료 문제).
      - `PUT <세션 URL>` 헤더 `Content-Type: application/octet-stream`,
        `--data-binary @<파일>` → 200이면 성공.
   3. `finalize_attachment({noteId, hash, sizeBytes, mimeType:
      "application/pdf", filename, sourceUrl})` → `enMediaTag`.
6. **본문 채우기:** `edit_note({noteId, mode:"append", content})` 한 번:
   - PDF `<en-media ... style="--en-viewAs:attachment;" />`
   - `paper`: arXiv abs 링크 + (있으면) `학술지 권, 쪽 (연도) — DOI 링크
     (첨부 PDF는 ...판)`
   - `title` / `authors` / `abstract`: 1단계 원문
   - `설명`: Claude가 대화에서 실제로 한 설명
   - `further reads`: 비워두거나 대화에서 함께 언급한 관련 논문
   본문은 python으로 조립해 파일로 만든 뒤 내용을 그대로 넘기면 이스케이프
   실수가 없다.

## 5. Babel 노트의 "Reading.." 맨 위에 넣기 — 필수

새 논문 노트를 하나라도 만들면 **항상** 실행한다. 주제 섹션(A~J)에는
이 단계에서 넣지 않는다.

1. `edit_note(mode:"replace")`, `find`는 `<b>Reading..</b></h2><ol>`
   (실제 헤딩 마크업은 `get_note`로 확인), `content`는 같은 문자열 뒤에 새
   `<li>`들을 붙인 것. 여러 편이면 한 번에, 사용자가 읽을 순서(또는 추천
   순서)대로 위에서부터 넣는다.
2. 항목 형식(기존 항목과 동일):
   ```
   <li><div><a href="evernote:///view/<account>/<shard>/<노트GUID>/<노트북GUID>/" rel="noopener noreferrer" rev="en_rl_none"><span style="color:rgb(24, 168, 65);"><노트 제목></span></a><span style="color:rgb(24, 168, 65);"> (<오늘 날짜, Month D, YYYY>) </span><en-todo checked="false" /></div></li>
   ```
   `<account>/<shard>`는 Reading..의 기존 항목 링크에서 그대로 복사한다.
3. Reading.. 항목을 개수 제한으로 지우지 않는다(예전의 "15개 넘으면
   삭제" 규칙은 폐지 — 읽은 것은 6단계처럼 주제 섹션으로 옮긴다).

## 6. 읽은 논문을 주제 섹션으로 옮기기

사용자가 "읽은 논문 정리해줘/옮겨줘"라고 하거나, 5단계로 Reading..을
갱신할 때 체크된 항목이 보이면 실행한다(옮기기 전에 목록을 보여주고
한 번 확인받는다).

1. Reading.. 안에서 `<en-todo checked="true" />`가 있는 `<li>`를 찾는다
   (한 항목에 체크박스가 여러 개일 수 있다 — 하나라도 체크돼 있으면 읽은
   것으로 본다. 확실치 않으면 사용자에게 묻는다).
2. 각 항목의 주제에 맞는 섹션을 고른다(섹션 제목이 주제다. 예: 얽힘·양자
   정보 → `D. [Library] QC, entanglement, Quantum info`, 일반 QCD →
   `G. [Library] QCD`의 알맞은 하위 목록). 애매하면 사용자에게 묻는다.
3. 그 섹션의 목록(`<ol>`/`<ul>` 또는 표 — 섹션마다 형식이 다르니 실제
   마크업을 보고 기존 항목 형식을 따른다) 끝에 그 `<li>`를 추가하고,
   Reading..에서는 그 `<li>`를 `content:""`로 replace해서 지운다. 링크·
   체크 상태는 그대로 옮긴다.

## 7. 검증 및 보고

- 새 노트가 고른 노트북에 실제로 있는지
  `search_notes({query:'notebook:"<노트북 이름>" created:day-1'})`로
  확인하고, 하나는 `get_note`로 열어 PDF 첨부와 여섯 섹션을 확인한다.
- Babel 노트의 replace가 정확히 한 번 매치해 성공했는지 확인한다.
- 사용자에게 짧게: 만든 노트 제목·노트북, PDF가 저널판인지 arXiv판인지
  (저널판 실패 이유), Reading..에 넣은 순서, 옮긴 항목(있다면)을 보고한다.

## 8. 개인정보 주의

[[evernote-weekly-todo]] 11절과 동일 — 이 스킬 문서(공개 repo)에는
실제 notebookId·noteId·Evernote 계정 shard 번호를 적지 않는다.
