---
name: research-card-sheet
description: 세종대 연구행정통합시스템(iacf.sejong.ac.kr)에서 과제별 연구비 카드 사용내역(지난 3개월, 미청구)을 받아, 이번 달 말 결제예정일자(예: 11월이면 20261126)인 건만 골라 Google Sheet로 올리고, 그 시트 링크(.webloc)를 과제별 Dropbox '<YYYY>년 <M>월' 폴더에 넣는다. 같은 김에 구독료(Claude/Gemini 등) 카드 건의 증빙(청구서·영수증 PDF)도 해당 과제 폴더에 넣는다. '연구비 카드 내역 올려줘', '카드건 엑셀로 올려', '이번 달 카드 내역 구글 시트로', 'EIC 과제 카드 내역 정리', '클로드/제미니 영수증 처리' 요청 시 사용. 2026-11-15 사용자 화면녹화로 학습.
---

# 연구비 카드 내역 → Google Sheet + 링크 (월말 정산용)

매달 말 연구비 카드 결제 전에, 과제별로 "이번 결제일에 빠져나갈 카드건" 목록을
Google Sheet로 만들어 링크를 Dropbox 월별 폴더에 둔다. 행정 담당자/사용자가 그
시트의 `사용자`·`링크` 칸(출장 증빙 zip 링크 등)을 채운다.

## 0. 규칙

- **로그인은 사용자 본인만.** iacf.sejong.ac.kr 로그인 화면이면 멈추고 로그인
  요청. ID/PW 입력·Keychain 접근 금지.
- 카드번호·시트 ID 등 실제 값은 이 SKILL.md(공개 git repo)에 적지 않는다.
- 시트 공유 범위(링크 공개 등) 변경은 사용자 확인 후에만.

## 1. 과제·폴더 대응 (2026-11 기준)

| 과제 | 시스템의 과제명 | Dropbox 월별 폴더 |
|---|---|---|
| 중견과제 (알파 클러스터, 5차년도) | `2022-0401-02` 핵속의 알파 다발이 만드는 보즈-아인슈타인 응집의 탐색 | `~/Library/CloudStorage/Dropbox/01. 개인서류/2022- 중견과제/<YYYY>년 <M>월/` |
| EIC 개별협력연구 (1차년도) | `2026-0437-01` EIC개발협력연구(1차년도) | `~/Library/CloudStorage/Dropbox/01. 개인서류/2026 - EIC 과제/<YYYY>년 <M>월/` |

과제마다 카드가 다르다(카드 끝 4자리로 구분: 시스템 '카드' 탭에서 확인).
구독료 결제 카드: **Gemini(Google One, 구글페이먼트코리아) → 중견과제 카드**,
**Claude(ANTHROPIC* CLAUDE SUB) → EIC 카드**.

## 2. 사용자 수동 흐름 (화면녹화에서 본 그대로)

1. iacf.sejong.ac.kr 로그인 → 메인 '알림'/'안내' 팝업 닫기
2. 상단 **과제관리** → 과제정보 화면 → 우측 **조회** 버튼 → '과제조회' 팝업에서
   과제 라디오 선택 → **확인**
3. 탭 중 **카드** 클릭 → 기간 **3개월**(오늘 기준 ±, 예: 09-15~12-15), 상태
   **미청구** → 조회
4. **다운로드** → '파일저장' 팝업 → 파일저장 → '개인정보 파일저장 사유'(5자 이상)
   입력 → 확인 → `~/Downloads/<YYYYMMDDhhmmssSSS>.xls` 저장
5. xls에서 결제예정일자가 이번 달 말 결제일인 건만 골라 Google Sheet 작성
6. 시트 링크를 `<YYYY>.<MM> 연구비 카드 내역 - Google Sheets.webloc`으로 해당 월 폴더에

## 3. Claude가 하는 방법 (claude-in-chrome)

- 새 탭에서 `https://iacf.sejong.ac.kr/rderp_layoutMain.act` 열기. 로그인돼 있으면
  진행. 팝업 닫기 → '과제관리' 클릭.
- **'과제조회'는 `window.open` 팝업이라 claude-in-chrome이 못 잡는다.** 조회
  누르기 전에 [[sejong-approval]] 3-B 방식으로 open을 가로챈다. 내용 프레임은
  top의 `frames[1]`(`rtask_0008_t00_01.act`):
  ```js
  window.open=function(url,name){const f=document.createElement('iframe');f.name=name||('p'+Date.now());f.id='__pop';
   f.style.cssText='position:fixed;top:40px;left:40px;width:1250px;height:700px;z-index:999999;background:white;border:3px solid red;';
   document.body.appendChild(f); if(url) f.src=url; return f.contentWindow;};
  for(let i=0;i<frames.length;i++){try{frames[i].open=window.open}catch(e){}}
  ```
  팝업 로드 후 **확인이 opener를 호출하므로** 반드시 연결:
  ```js
  const f=document.getElementById('__pop'), w=f.contentWindow; w.opener=frames[1]; w.close=()=>f.remove();
  ```
  그 다음 과제 라디오 → 확인을 좌표 클릭하면 과제가 선택된다.
- '카드' 탭 클릭 → 기본값이 이미 3개월·미청구로 조회된다(아니면 3개월/미청구/조회).
- 건수가 적으면 **그리드를 직접 읽어도 된다**(zoom 스크린샷 또는 get_page_text):
  결제예정일자·사용일·사용일시·승인번호·사용구분·가맹점·가맹점업종·사용액·공급가액.
  건수가 많으면 다운로드(2절 4단계, 사유는 예: `연구비 카드 정산 자료`) 후 xls를
  `pandas.read_excel(..., dtype=str)`로 읽는다(`xlrd` 필요). 사용자가 이미 받아둔
  오늘자 xls가 `~/Downloads`에 있으면 그걸 쓴다 — 단, 카드번호 열로 어느 과제
  것인지 확인(같은 과제를 두 번 받아둔 경우가 있었다).
- 마지막 합계행(빈 행)은 버린다. 취소건(음수 사용액)도 결제예정일이 같으면 그대로 포함.

## 4. Google Sheet 형식 (2026.10 시트와 동일)

헤더: `결제예정일자, 사용일, 사용일시, 승인번호, 사용구분, 가맹점, 가맹점업종, 사용액, 공급가액, 사용자, 링크`
- 날짜는 `YYYYMMDD`, 시각은 `hhmmss` 그대로. `사용자`·`링크`는 빈칸(나중에 채움 —
  출장건이면 출장자 이름과 증빙 zip 링크).
- `mcp__claude_ai_Google_Drive__create_file`에 `contentMimeType: text/csv`로 올리면
  스프레드시트로 변환된다. 제목: `<YYYY>.<MM> 연구비 카드 내역` (EIC는 뒤에
  ` (EIC 1차년도)` 붙임).
- webloc: `plutil -create xml1 X.webloc; plutil -insert URL -string "<url>/edit?gid=0#gid=0" X.webloc`

## 5. 구독료 증빙 (같은 월 폴더에)

파일명은 `<사용일 YYYY.MM.DD>_<카드 사용액>원_<서비스>.pdf`.
- **Claude**: claude.ai → Settings → Billing → Invoices → 해당 월 'Download PDF'
  (`~/Downloads/Invoice-XXXX.pdf`). 청구서 금액(원화)과 카드 사용액은 해외결제
  수수료만큼 다르다(예: 179,637 vs 183,648) — 파일명은 카드 사용액 기준, 차이를
  보고에 언급. → **EIC 폴더**.
- **Gemini(Google AI Pro)**: Gmail `from:googleplay-noreply@google.com "Order Receipt"`
  메일 본문을 HTML로 정리 → Chrome headless
  `--headless=new --no-pdf-header-footer --print-to-pdf=...`로 PDF. → **중견과제 폴더**.
- 시트에 있는 다른 건의 영수증이 이미 다른 폴더(예: `2022- 중견과제/영수증들/`)에
  있으면, 그 건의 카드가 어느 과제인지 보고 해당 과제 월 폴더에 **복사**한다.

## 6. 보고

과제별 건수·사용액 합계(시스템 화면 합계와 일치 확인), 시트 링크, 폴더에 넣은
파일 목록, 금액 차이·애매한 건, 공유 설정을 바꾸지 않았다는 점.
