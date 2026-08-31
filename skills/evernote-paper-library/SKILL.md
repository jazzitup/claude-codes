---
name: evernote-paper-library
description: "Claude가 리서치/토론 중에 추천하거나 논의한 논문 목록(직접 링크를 준 게 아니라 '이 논문들 저장해줘'처럼 대화 맥락에서 나온 여러 편)을 Evernote 논문 라이브러리에 일괄 정리한다. 논문마다 노트를 만들어 paper 링크/title/authors/abstract(전부 원문 그대로)와 Claude 자신의 설명(왜 관련 있는지, 대화에서 실제로 한 말)을 적고 PDF를 첨부한 뒤, 'La Bibliothèque de Babel' 노트의 해당 주제 섹션(A~J 등)에 링크를 걸고, 그 노트의 'Reading..' 섹션을 전체 라이브러리에서 가장 최근에 추가된 15편으로(최신이 위로, 이미 체크된=읽은 항목은 제외) 갱신한다. [[evernote-paper-to-read]]와 다른 점: 그 스킬은 사용자가 직접 준 링크 1개를 '[T] To read' 노트북에 4필드(paper/title/authors/abstract)로 저장하는 단순 케이스이고, 이 스킬은 여러 편을 한 번에, '설명' 필드까지 포함해서, 별도의 '논문 라이브러리' 노트북(La Bibliothèque de Babel과 짝을 이루는 곳)에 저장하고 Babel 색션·Reading 리스트까지 갱신하는 확장 케이스다. '이 논문들 에버노트에 저장해줘', '방금 추천한 논문들 라이브러리에 넣어줘', '바벨 도서관 D 섹션에 링크 걸어줘', 'Reading 리스트 갱신해줘' 요청 시 사용."
---

# Evernote 논문 라이브러리 일괄 정리 (paper note + Babel 링크 + Reading 리스트)

## 0. 배경

사용자는 물리학 논문을 Evernote에 노트 한 편씩 정리해서 모아두는 노트북을
쓰고, 그 목차 역할을 하는 노트가 **"La Bibliothèque de Babel"**이다. 이
노트 안에 주제별 섹션(`A. [Library] nucl-th & nucl-ex`, `B. [Library]
p_c, p_s, quarkonia, UPC, X(3872)`, ... `D. [Library] QC, entanglement,
Quantum info` 등, `A`~`J` 정도)이 있고, 각 섹션은 그 주제에 속한 논문
노트로 가는 내부 링크(`evernote:///view/...`) 목록이다. 맨 위에는
**"Reading.."** 섹션이 있어, 지금 읽고 있는/읽을 논문들의 지름길 역할을
한다.

이 스킬은 [[evernote-paper-to-read]](사용자가 준 링크 1개를 간단한
4필드로 `[T] To read` 노트북에 저장하는 스킬)와는 별개다 — 이쪽은
**여러 편을 한 번에**, **Claude 자신의 코멘트("설명")까지 포함해서**,
**"논문 라이브러리" 노트북**(Babel과 짝을 이루는, 아래 1단계에서 매번
새로 찾는 곳)에 저장하고, **Babel 노트의 관련 섹션과 Reading 리스트까지
갱신**하는 확장된 절차다.

## 0.1 핵심 원칙 (다른 Evernote 스킬과 동일)

- **서식을 손으로 재현하지 않는다.** 항상 실제 예시 노트를 `get_note`로
  읽어서 그 ENML(라벨, 색상, 폰트, 링크 구성)을 그대로 본떠 쓴다.
- **title/authors/abstract는 원문 그대로.** arXiv API/INSPIRE-HEP
  메타데이터에서 가져온 원문을 절대 의역·요약하지 않는다. abstract에
  MathML(`<math>...</math>`)이 섞여 나오는 경우(특히 INSPIRE API)는
  ENML이 깨지므로 유니코드 텍스트로 치환한다(예:
  `<math>...u...</math>` → `uū`).
- **"설명"은 Claude가 실제로 한 말이다.** 대화 중에 그 논문을 왜
  추천했는지 실제로 설명한 내용을 그대로(또는 자연스럽게 다듬어) 적는다
  — 지어내지 않는다. 이 필드가 이 스킬을 [[evernote-paper-to-read]]와
  구별 짓는 핵심 추가 요소다.
- **이 SKILL.md(공개 git repo)에는 실제 notebookId·noteId·계정
  번호(예: `6010485/s28` 같은 shard)를 적지 않는다.** 아래 모든 단계는
  "그때그때 검색해서 찾는" 절차로 적는다 — 실제 값은 실행 시점에
  `search_notes`/`get_note`로 읽어온다.

## 1. Evernote MCP 연결 확인

`mcp__evernote__*` 도구가 없으면 사용자에게 알리고 멈춘다
([[evernote-weekly-todo]] 10절 참고).

## 2. 대상 노트북(논문 라이브러리) 찾기

1. `search_notes({query: "intitle:\"La Bibliothèque de Babel\""})`로 목차
   노트를 찾는다.
2. 그 노트 안의 각 섹션 링크(`evernote:///view/<account>/<shard>/<noteId>/<notebookId>/`)
   에서 `<notebookId>` 부분을 뽑아내면 논문 라이브러리 노트북의 GUID다
   (Babel 노트 자체와 논문 노트들이 서로 다른 노트북에 있을 수 있으니,
   섹션 안의 개별 논문 링크에서 뽑아야 한다 — Babel 노트 자신의
   notebookId가 아니다).
3. 확인용으로 그 notebookId로 `search_notes({query:
   "nbGuid:\"<notebookId>\""})`를 돌려 "저자 (연도) 제목" 형식의 논문
   노트들이 실제로 나오는지 확인한다.

## 3. 서식 참고 노트 읽기

1. 2단계에서 찾은 노트북 안에서 최근 논문 노트 하나(예: 최근 만든 것)를
   `get_note`로 읽어 ENML 구조를 파악한다.
2. 확인할 것:
   - `paper`(원문 링크, 있는 경우) / `title` / `authors` / `abstract` /
     `further reads` 각 라벨의 정확한 헤딩 스타일(`<h1>` +
     monospace span + font-size)
   - PDF 첨부가 노트 맨 앞에 `<en-media type="application/pdf"
     hash="..." />` 형태로 들어가 있는지
   - "설명"(또는 비슷한 코멘트) 필드가 이미 있는 예시가 있는지 — 없으면
     `abstract`와 `further reads` 사이에 새로 넣는다(4단계 참고).

## 4. 논문마다 노트 만들기

논문이 여러 편이면 4~7단계를 논문마다 반복한다.

1. **메타데이터 수집**: arXiv 링크면
   `http://export.arxiv.org/api/query?id_list=<ID>` (Atom XML) 또는
   INSPIRE-HEP API(`https://inspirehep.net/api/literature?q=eprint
   <ID>&fields=titles,authors,abstracts,arxiv_eprints,publication_info`)
   에서 title/authors/abstract를 원문 그대로 가져온다. INSPIRE
   abstract에 `<math>` 태그가 섞여 있으면 유니코드로 치환(위 0.1절).
   대형 협업 논문(ATLAS/CMS/STAR 등)은 저자 수백~수천 명을 나열하지
   말고 `"<실험명> Collaboration"`으로 적는다(예: `STAR
   Collaboration`).
2. **노트 제목**: `"<저자(들)> (<연도>) <논문 제목>"` 형식 — 저자가
   1~3명이면 성만 나열(`Low, Yin`), 4명 이상이면 `<제1저자 성> et al.`,
   대형 협업이면 `<실험명> Collaboration`. 라이브러리의 기존 제목들과
   일관되게 맞춘다.
3. `mcp__evernote__create_note({title, notebookId})`로 빈 노트 생성.
4. PDF를 스크래치패드에 받는다: arXiv면 `curl -sL
   https://arxiv.org/pdf/<ID> -o <파일>` (Nature/저널판만 있고 arXiv
   프리프린트가 없으면 오픈 액세스 사본을 찾고, 그마저 없으면 PDF
   생략 — [[evernote-paper-to-read]] 6절과 동일한 원칙). `file`로 실제
   PDF인지 확인.
5. PDF 첨부(3단계 API 흐름 — 매번 스키마가 바뀔 수 있으니 실행 시점에
   도구 설명을 다시 확인):
   1. 파일의 MD5(`md5 -q <파일>`)와 바이트 크기(`stat -f%z <파일>`)를
      구한다.
   2. `mcp__evernote__start_attachment_upload({noteId, hash, sizeBytes})`
      → `uploadUrl` 받음. `alreadyUploaded:true`면 업로드 생략, 아니면:
      - `POST <uploadUrl>` 헤더 `x-goog-resumable: start`,
        `content-length: 0`, `x-upload-content-length: <size>` → 응답의
        `Location` 헤더가 세션 URI.
      - `PUT <세션 URI>` 헤더 `Content-Length: <size>`, 바디 =
        `--data-binary "@<파일>"`. 200이면 성공.
   3. `mcp__evernote__finalize_attachment({noteId, hash, sizeBytes,
      mimeType:"application/pdf", filename, sourceUrl})` →
      `enMediaTag` 받음.
6. 본문 조립(3단계에서 파악한 서식 그대로) 후
   `mcp__evernote__edit_note({noteId, mode:"append", content})`로 채운다:
   - PDF `<en-media>` 태그 (5단계 결과)
   - `paper` 섹션: 원문 링크(arXiv abs 페이지 등)
   - `title` / `authors` / `abstract` 섹션: 1단계에서 가져온 원문
   - **`설명` 섹션**: Claude가 대화 중 그 논문을 언급하며 실제로 한
     설명(왜 관련 있는지, 어떤 맥락)을 적는다
   - `further reads` 섹션: 비워두거나(사용자가 나중에 채움), 이미
     대화에서 관련 논문을 언급했으면 채운다
   - `content`는 정돈된 XML(`&`→`&amp;`, `<`→`&lt;`)이어야 한다.

## 5. La Bibliothèque de Babel의 주제 섹션에 링크 걸기

1. Babel 노트를 `get_note`로 읽는다(내용이 커서 도구가 파일로 저장해줄
   수 있다 — 그러면 그 파일을 읽는다).
2. 논문 주제에 맞는 섹션(`A.`~`J.` 각각의 부제로 주제를 파악, 예:
   entanglement/양자정보 계열이면 `[Library] QC, entanglement, Quantum
   info` 섹션)을 찾는다. 애매하면 사용자에게 어느 섹션인지 확인한다.
3. 그 섹션의 `<ol>...</ol>` 안 **마지막 `<li>`**를 찾아, 그 `<li>`의
   고유한 텍스트(예: 마지막 항목 제목)를 포함해서 `find` 앵커로 삼는다
   (예: `...<span>마지막 항목 제목</span></a><en-todo
   checked="false" /></div></li></ol>`).
4. 그 자리에 새 `<li>` 항목들을 `</ol>` 앞에 이어붙인다. 항목 형식은
   기존 항목과 동일하게:
   ```
   <li><div><a href="evernote:///view/<account>/<shard>/<노트GUID>/<노트북GUID>/" rel="noopener noreferrer" rev="en_rl_none"><span style="color:rgb(24, 168, 65);"><노트 제목></span></a><en-todo checked="false" /></div></li>
   ```
   `<account>/<shard>`는 같은 섹션의 기존 링크에서 그대로 복사한다(계정
   고정값이라 매번 같다). `mcp__evernote__edit_note(mode:"replace")`로
   반영.

## 6. "Reading.." 섹션을 최근 15편으로 갱신

1. 2단계에서 찾은 논문 라이브러리 notebookId로
   `search_notes({query: "nbGuid:\"<notebookId>\"", sortBy: "created",
   ascending: false, maxResults: 15})`를 돌려 **라이브러리 전체에서
   가장 최근에 만든 15개 노트**(이번에 새로 만든 것 포함)를 가져온다.
2. Babel 노트에서 현재 "Reading.." 섹션(`<h2>...Reading..</h2>` 바로
   다음 `<ol>...</ol>`)을 읽어, 이미 체크(`<en-todo checked="true"
   />`)된 항목이 있는지 확인한다 — **체크된 항목은 이미 읽은 것이므로
   새 리스트에서 뺀다**(사용자가 직접 체크 → 다음 갱신 때 자동으로
   빠지는 것이 이 규칙의 목적).
3. 새 리스트를 구성한다: 1단계에서 가져온 순서(최신 우선)대로 넣되,
   2단계에서 이미 체크된 것으로 확인된 노트는 건너뛰고, 15개가 될
   때까지 그다음 최근 노트로 채운다(`maxResults`를 15보다 좀 크게, 예:
   20~25로 늘려서 여유분을 확보해두면 편하다).
4. 각 항목 형식(기존 D섹션 항목과 같은 링크 스타일 + 날짜 + 체크박스):
   ```
   <li><div><a href="evernote:///view/<account>/<shard>/<노트GUID>/<노트북GUID>/" rel="noopener noreferrer" rev="en_rl_none"><span style="color:rgb(24, 168, 65);"><노트 제목></span></a><span style="color:rgb(24, 168, 65);"> (<Month D, YYYY>) </span><en-todo checked="false" /></div></li>
   ```
   날짜는 그 노트의 `createdAt`을 `Month D, YYYY` 형식(예: `August 31,
   2026`)으로 변환한 값 — Babel 노트의 다른 섹션에서 실제로 쓰는
   날짜 표기와 동일한 스타일이니 그대로 맞춘다.
5. `mcp__evernote__edit_note(mode:"replace")`로 "Reading.." 섹션의
   `<h2>...Reading..</h2><ol>...</ol>` 전체를 통째로 새 리스트로
   교체한다(부분 추가가 아니라 매번 전체 재구성 — 순서·체크 상태
   일관성을 위해).

## 7. 검증 및 보고

- 새로 만든 논문 노트마다 `get_note`로 다시 읽어 PDF 첨부와 다섯(또는
  여섯: paper/title/authors/abstract/설명/further reads) 섹션이 제대로
  들어갔는지 확인한다.
- Babel 노트를 다시 읽어(또는 방금 반영한 `find`/`content`가 정확히
  한 번만 매치해 성공했는지로 간접 확인) 주제 섹션 링크와 Reading
  리스트가 의도대로 반영됐는지 확인한다.
- 사용자에게 짧게: 만든 노트 제목 목록, PDF 첨부 성공/실패 여부(실패
  이유 포함), Babel 어느 섹션에 넣었는지, Reading 리스트에서 빠진(이미
  체크됐던) 항목이 있었는지를 보고한다.

## 8. 개인정보 주의

[[evernote-weekly-todo]] 11절과 동일 — 이 스킬 문서(공개 repo)에는
실제 notebookId·noteId·Evernote 계정 shard 번호를 적지 않는다. 실제
값은 실행 시점에 매번 `search_notes`/`get_note`로 새로 읽어온다.
