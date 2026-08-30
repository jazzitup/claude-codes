---
name: evernote-paper-to-read
description: "사용자가 논문 링크(arXiv/저널/DOI 등, 여러 개 가능)를 주면 기존 Evernote 노트 'Quantum Sensing Radiative Decays of Neutrinos and Dark Matter Particles'와 같은 구조(paper 링크, title, authors, abstract, further reads)로 새 노트를 만들고 논문 PDF를 다운로드해 첨부한 뒤 '04. Library' 스택의 '[T]To read' 노트북에 넣는다. 제목·저자·초록은 arXiv API/논문 페이지에서 실제 값을 그대로 가져오고 절대 지어내지 않으며, further reads는 실재하는 관련 논문만 검색해서 채운다. PDF는 원 링크가 유료/접근불가면 arXiv 등 오픈 액세스 버전에서 대신 받는다. Evernote MCP(https://mcp.evernote.com/mcp)가 연결되어 있어야 동작한다 — 연결 방법은 [[evernote-weekly-todo]] 10절 참고. '이 논문 에버노트에 넣어줘', '이 arXiv 링크 투 리드에 추가해줘', '논문 라이브러리에 저장해줘', 'Library에 논문 추가', 'PDF도 받아서 넣어줘' 요청 시 사용."
---

# Evernote "읽을 논문" 노트 생성 (04. Library → [T]To read)

사용자는 Evernote의 **"04. Library"** 스택 안 **"[T]To read"** 노트북에 논문
한 편당 노트 한 개씩 정리해 둔다. 기존 예시가
**"Quantum Sensing Radiative Decays of Neutrinos and Dark Matter Particles"**
노트이며, 필드 구성은 **paper(링크) / title / authors / abstract /
further reads** 다. 이 스킬은 사용자가 새 논문 링크를 주면 같은 구조로 새
노트를 만들어 같은 노트북에 넣는 절차다.

## 0. 핵심 아이디어

- **필드 라벨·서식·순서를 손으로 재현하지 않는다.** [[evernote-weekly-todo]]
  스킬과 같은 원칙이다 — 항상 실제 예시 노트("Quantum Sensing Radiative
  Decays...")를 `get_note`로 읽어서 그 ENML 구조(라벨 텍스트, 굵기/스타일,
  링크를 거는 방식, further reads 항목의 형식)를 그대로 본떠 쓴다. 이 문서에
  구체적인 HTML을 박아두지 않는 이유는, 실제 값은 그때그때 `get_note`로
  읽어야 정확하고(사람이 에디터에서 다듬은 서식은 재현하면 미묘하게 달라짐),
  예시 노트 자체가 나중에 바뀔 수도 있기 때문이다.
- **title/authors/abstract는 논문의 실제 값을 그대로 가져온다 — 절대
  의역하거나 지어내지 않는다.** arXiv API나 논문 페이지의 메타데이터에서
  가져온 원문 그대로 넣는다.
- **further reads는 실재하는 논문만 넣는다.** 존재하지 않는 논문 제목·링크를
  만들어내는 것(hallucination)은 이 스킬에서 가장 위험한 실패 모드다 —
  WebSearch/WebFetch로 실제로 검색되고 링크가 열리는 것만 최종 후보로
  남긴다.

## 1. 입력 파싱

- 사용자가 논문 링크를 하나 또는 여러 개 줄 수 있다. 링크가 여러 개면 논문별로
  이 절차를 순서대로 반복한다(한 번에 노트 여러 개 생성).
- 링크 형태 예시: `arxiv.org/abs/XXXX.XXXXX`, `arxiv.org/pdf/XXXX.XXXXX`,
  저널 DOI 링크, INSPIRE-HEP 링크 등. arXiv 링크면 `XXXX.XXXXX` 형태의 ID를
  정규식으로 뽑아둔다 — 3단계에서 API 호출에 쓴다.

## 2. Evernote MCP 연결 확인

`mcp__evernote__*` 도구가 이 세션에 없으면 사용자에게 알리고 멈춘다
([[evernote-weekly-todo]] 10절 — `claude mcp login evernote` 후 세션 재시작
필요). 다른 백그라운드 체크(예: [[evernote-daily-checkin]])처럼 조용히
넘어가지 않는다 — 이 스킬은 사용자가 명시적으로 요청한 작업이므로 연결이
안 되어 있으면 반드시 알린다.

## 3. 참고 노트 구조 읽기

1. `mcp__evernote__search_notes({query: "intitle:\"Quantum Sensing Radiative Decays of Neutrinos and Dark Matter Particles\""})`로 참고 노트를 찾는다.
2. `get_note`로 본문 ENML 전체를 읽는다. 다음을 파악한다:
   - `paper` 필드가 어떤 라벨/서식으로 표시되고 링크가 어떻게 걸려 있는지
     (예: `<a href="...">`)
   - `title`/`authors`/`abstract` 라벨의 정확한 텍스트와 스타일(굵게, 폰트
     크기, 콜론 유무 등)
   - `further reads`가 목록(`<ul>`/`<li>`)인지, 항목 하나당 제목+링크만
     있는지 한 줄 설명이 붙어 있는지
   - 노트 제목(note title) 자체가 논문 제목과 동일한지
3. 이 구조를 그대로 재사용할 골격(스캐폴드)으로 삼는다 — 라벨과 서식은 복사,
   내용만 새 논문 것으로 교체.

## 4. 논문 메타데이터 수집 (title / authors / abstract)

- **arXiv 링크인 경우**: `WebFetch`로
  `http://export.arxiv.org/api/query?id_list=<arXiv ID>`를 호출해 Atom XML
  응답에서 `<title>`, `<author><name>`(전부), `<summary>`(abstract)를
  그대로 추출한다. 줄바꿈/공백만 정리하고 문장은 손대지 않는다.
- **arXiv가 아닌 경우**(저널 페이지, DOI 리다이렉트 등): `WebFetch`로 페이지를
  가져와 `citation_title`/`citation_author`/`citation_abstract`
  meta 태그나 눈에 보이는 Title/Authors/Abstract 영역에서 그대로 가져온다.
  meta 태그가 없으면 페이지에 실제로 보이는 텍스트만 쓰고, 확신이 안 서는
  필드는 사용자에게 확인을 구한다(지어내지 않는다).
- authors는 참고 노트의 서식(전체 이름 나열 방식 — 콤마 구분인지, "et al."
  축약인지)을 그대로 따른다. 저자가 아주 많은 협업 논문(예: 대형 실험
  컬래버레이션)이면 참고 노트에 비슷한 사례가 있는지 보고 그 처리 방식을
  따르되, 없으면 전체 나열하거나 컬래버레이션 이름 + "et al."로 사용자와
  확인한다.

## 5. Further reads 수집

목표: 이 논문과 주제가 겹치는 **실재하는** 논문 2~5편(참고 노트의 개수/형식에
맞춤)을 찾아 제목+링크(+참고 노트 형식에 한 줄 설명이 있으면 한 줄 설명도)로
정리한다.

방법:
1. arXiv 논문이면 INSPIRE-HEP(`inspirehep.net`)이나 arXiv 자체의
   "references"/"citations" 정보, 또는 WebSearch로 같은 주제(예: 저자가
   같은 후속 연구, 논문 초록에 언급된 핵심 선행연구)를 찾는다.
2. 후보 각각을 `WebFetch`나 `WebSearch` 결과로 **실제로 링크가 열리고
   제목이 검색 결과와 일치하는지 검증**한 것만 최종 목록에 남긴다. 검증 안
   된 항목은 절대 넣지 않는다.
3. 원 논문과 지나치게 겹치는 항목(같은 저자의 사실상 같은 논문 중복판)이나
   지나치게 일반적인 교과서급 리뷰만 나열하지 말고, 실제로 이 논문을 더
   깊이 이해하는 데 도움되는 것(핵심 선행연구, 방법론 원 논문, 직접적인
   후속연구)을 우선한다.

## 6. PDF 다운로드

1. 논문 PDF를 스크래치패드 디렉터리에 받는다.
   - arXiv 링크(또는 4단계에서 arXiv 대응본을 찾은 경우): `https://arxiv.org/pdf/<arXiv ID>`를
     `curl -sL`로 받는다(`http://export.arxiv.org/...`처럼 리다이렉트가 걸리는
     호스트가 있으니 `-L` 필수). 파일명은 `<제1저자 성_연도_논문제목 앞부분>.pdf`
     처럼 알아보기 쉽게 짓는다.
   - 논문 자체가 오픈 액세스 PDF를 직접 제공하면(예: Nature Communications,
     PMC, 학회 무료 배포본) 그 링크를 받는다.
   - **원래 사용자가 준 링크가 유료 저널 페이지라 PDF에 직접 접근할 수 없으면**
     (APS/Elsevier/Springer 등에서 403/유료 안내가 뜨는 경우), WebSearch로 같은
     논문의 arXiv/저자 공개본(author's accepted manuscript)이 있는지 찾아서
     대신 그걸 받는다 — DOI나 논문 제목으로 검색하면 대개 찾을 수 있다. 그마저
     없으면 PDF 첨부는 생략하고 6단계 이하는 건너뛰되, **왜 PDF를 못 받았는지
     보고에 명시**한다(예: "저널판은 구독 필요, 오픈 액세스 사본도 못 찾음").
2. `file`로 다운로드된 파일이 실제 PDF인지 확인한다(HTML 에러 페이지가 잘못
   저장되는 경우가 있다 — `PDF document`가 아니면 실패로 간주하고 재시도하거나
   생략).

## 7. PDF 첨부

Evernote 노트에 파일을 첨부하는 방식은 MCP 서버 스키마에 따라 다를 수 있으므로,
**실행 시점에 실제 도구 스키마를 확인**한다(예: `mcp__evernote__create_note`나
`mcp__evernote__edit_note`에 `resources`/`attachments`류 파라미터가 있는지,
또는 별도의 `mcp__evernote__add_resource`류 도구가 있는지). 스키마가 파일 경로를
받으면 6단계에서 받은 로컬 경로를 그대로 넘기고, base64 데이터를 요구하면
인코딩해서 넘긴다. 노트 본문(ENML)에 `<en-media type="application/pdf" hash="..."/>`
같은 참조가 필요한 방식이면, 참고 노트에도 PDF가 첨부돼 있는지 `get_note`로 확인해
그 구조(첨부가 본문 안에 인라인으로 보이는지, 노트 하단에 별도로 붙는지)를 그대로
따른다.

## 8. 대상 노트북 찾기

1. `mcp__evernote__search_notebooks`로 이름에 "To read"가 들어간 노트북을
   찾는다. 여러 개 후보가 나오면 `stack` 필드(또는 API가 제공하는 노트북
   계층 정보)로 **"04. Library"** 스택 소속인지 확인해 `[T]To read`
   노트북의 `notebookId`를 확정한다.
2. 이름이나 스택이 애매하면(대괄호 표기 `[T]`가 검색에서 다르게 잡히는 등)
   후보를 사용자에게 보여주고 확인받는다 — 잘못된 노트북에 생성하는 것보다
   한 번 더 확인하는 게 낫다.

## 9. 노트 생성

1. 노트 제목 = 논문 제목(참고 노트가 그랬던 것처럼).
2. 3단계에서 파악한 골격에 다음을 채운 ENML 본문을 만든다:
   - `paper`: 원래 사용자가 준 링크(또는 arXiv면 정식 abs 페이지 URL)로
     하이퍼링크
   - `title`: 4단계에서 가져온 원문 제목
   - `authors`: 4단계에서 가져온 저자 목록
   - `abstract`: 4단계에서 가져온 원문 초록 그대로(요약/의역 금지)
   - `further reads`: 5단계에서 검증한 목록
   - PDF 첨부: 6~7단계에서 받은 파일을 7단계에서 파악한 방식대로 붙인다
     (PDF를 못 받았으면 첨부 없이 나머지만 채운다).
3. `content`는 정돈된 XML이어야 한다 — bare `&`, `<`는 `&amp;`, `&lt;`로
   이스케이프.
4. `mcp__evernote__create_note({title, notebookId, content, ...})`로 생성한다
   (또는 참고 노트가 ENML envelope가 특이하면 빈 노트 생성 후
   `edit_note(mode:"append")`로 채우는 [[evernote-weekly-todo]] 8절 방식을
   따라도 된다). PDF 첨부가 노트 생성과 별도 호출(예: `add_resource`)로
   이루어지는 스키마라면 노트 생성 후 이어서 호출한다.

## 10. 검증 및 보고

`get_note`로 새 노트를 다시 읽어 다섯 필드와 PDF 첨부가 의도한 대로 들어갔는지,
노트북이 맞는지(`notebookId`) 확인한다. 사용자에게는 노트 제목, PDF 첨부 여부
(못 받았으면 이유), further reads로 넣은 항목 목록을 짧게 보여주고, **further
reads는 자동 검색 결과이니 관련성이 떨어지는 게 있으면 알려달라**고 덧붙인다
(추측이 섞일 수 있는 유일한 필드라 검토를 유도).

## 11. 여러 편을 한 번에 요청받은 경우

논문 링크를 여러 개 준 요청이면 3~10단계를 논문마다 반복하되, 3단계(참고 노트
구조 읽기)와 8단계(노트북 찾기)는 첫 논문 처리 때 한 번만 하고 결과를 재사용
한다(같은 세션 안에서 구조나 노트북이 바뀔 리 없음). 전부 끝난 뒤 생성된 노트
제목 목록을 한 번에 정리해서 보고한다.
