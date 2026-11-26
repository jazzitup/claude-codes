---
name: qm2027-collab-reply-tracker
description: >-
  QM2027 parallel-talk acceptance 메일("Quark Matter 2027 — Accepted parallel talks of the <X> Collaboration",
  2026-11-26 발송)에 각 collaboration이 보낸 회신을 Gmail과 로컬 Mail.app(CERN Exchange)에서 찾아,
  'QM2027_parallel_selection_invitation list' 구글 시트의 'Collaboration Talks' 탭에 offer 수락 여부·merge 동의 여부·메모로
  기록한다. '답 온 곳 시트에 업데이트해', 'collaboration 회신 확인해', '수락/merge 동의 왔는지 정리해' 요청 시 사용.
user-invocable: true
---

# QM2027 collaboration 회신 → 시트 업데이트

## 0. 원칙
- **읽기와 시트 기록만 한다.** 회신 메일에 답장하거나 forward하지 않는다(메일은 사용자가 직접 보낸다).
- 회신 내용을 **과장하지 않는다**: "논의하겠다"는 동의가 아니다. 명시적으로 수락/동의한 경우에만 "수락"/"동의"라고 적는다.
- 이미 사람이 적어 둔 값은 지우거나 덮어쓰지 않는다. 값이 바뀌면 메모 칸에 날짜와 함께 덧붙인다.
- 공개 저장소이므로 이 파일에 수신자 개인 주소나 회신 본문을 적지 않는다.

## 1. 시트 찾기
- QM2027 폴더(Google Drive `My Drive/개인서류 drive/QM2027`)의
  `QM2027_parallel_selection_invitation list.gsheet` 파일은 JSON이다. 여기서 `doc_id`를 읽는다.
- 탭: `Collaboration Talks`. 열 구성:
  A Collaboration · B Id · C Title · D Result · E Selected track · F Merging suggestion ·
  G Merging partner selected? · **H Confirmed by Liaison**(트랙 liaison 확인용. collaboration 회신 칸이 아니므로 건드리지 않는다) ·
  I 사무국 인디코 처리.
- collaboration 회신 칸은 2026-11-26에 추가했다:
  - **J** "Collab 회신: offer 수락?"
  - **K** "Collab 회신: merge 동의?"
  - **L** "Collab 회신 메모 (날짜·회신자)"
  이 칸들은 **Accepted 행에만** 채운다(merge가 Accepted 행 기준으로 제안됐기 때문).
- 행 번호는 매번 `get_values`로 다시 찾는다. 시트가 바뀌었을 수 있으니 하드코딩하지 않는다.

## 2. 회신 찾기 (두 곳 모두 확인)
1. **Gmail** (`mcp__claude_ai_Gmail__search_threads`):
   `subject:"Accepted parallel talks" newer_than:30d`, view `THREAD_VIEW_SUMMARY`.
   - `messageCount` > 1인 스레드만 회신이 있는 것이다.
   - `get_thread`로 본문을 읽는다.
   - co-LOC 구글그룹이 cc에 있으면 회신이 Gmail로도 온다. 회신자가 그룹을 cc에서 빼면 Gmail에는 오지 않는다.
2. **Mail.app CERN Exchange 계정** (회신 대부분은 발신 주소로 바로 온다):
   ```applescript
   tell application "Mail"
     set mb to mailbox "Inbox" of account "Exchange"
     set msgs to (messages of mb whose date received > ((current date) - 30*days) and subject contains "Accepted parallel talks")
     -- date received / sender / subject / content
   end tell
   ```
   - `Re:` 외에 `Fwd:`나 제목이 바뀐 회신도 있을 수 있다. collaboration 이름과 "QM2027"로도 한 번 더 찾아본다.
3. 같은 회신이 두 곳에 다 있으면 하나로 친다.
4. 회신마다 다음을 판정한다:
   - offer 수락: `수락` / `거절` / `미확정 (언급 없음)`
   - merge 동의: `동의` / `일부 동의(어느 쌍)` / `거절` / `내부 논의 중` / `해당 없음`(merge 제안이 없는 collaboration, 예: HADES)
   - talk별로 답이 다르면 행마다 다르게 적는다.

## 3. 시트 기록
- `mcp__claude_ai_Google_Sheets__update_values`로 해당 Accepted 행의 J:L에 쓴다.
- L 칸 형식: `M/D <회신자 이름> 회신: <한 줄 요약>`.
  - 같은 collaboration의 두 번째 행부터는 `(위와 같음)`으로 짧게 적어도 된다.
- 이전 상태(예: "내부 논의 중")가 최종 답으로 바뀌면 J/K는 새 값으로 바꾼다.
  L에는 이전 메모를 지우지 않고 `; M/D ...`를 뒤에 덧붙인다.

## 4. 보고
- 표로 보고한다: collaboration / 회신 여부 / 수락 / merge / 회신자·날짜.
- 아직 회신이 없는 collaboration을 따로 적는다. 마감일(2026-11-30)이 가까우면 리마인더가 필요하다고 짚는다.
- QM2027 폴더 세션이면 `QM2027_work_log.md`에도 기록한다(그 폴더의 CLAUDE.md 규칙).
