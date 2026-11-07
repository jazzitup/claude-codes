---
name: evernote-note-shortcut
description: "사용자가 Evernote 노트 링크(evernote:///view/… 또는 노트 GUID)를 주고 '이 노트 바로가기를 X 폴더에 넣어', '더블클릭하면 에버노트에서 열리게 해줘'라고 하면, 그 폴더에 더블클릭 한 번으로 Evernote 앱이 해당 노트를 여는 작은 .app(osacompile로 만든 AppleScript 애플릿, Evernote 아이콘)을 만든다. 파일 이름은 노트 제목으로 짓는다(제목은 Evernote MCP get_note로 가져옴). .webloc/.inetloc은 evernote:// 스킴에서 `open`이 -10400으로 실패하므로 쓰지 않는다. 확인은 Evernote 창 제목이 아니라(창 제목은 노트북 이름만 보여줌) 화면 캡처로 한다. '에버노트 노트 바로가기 만들어', '노트 링크 파일로 저장해', 'Finder에서 바로 열리게' 요청 시 사용."
---

# Evernote 노트 바로가기(.app) 만들기

Finder의 폴더 안에 두고 더블클릭하면 Evernote 앱에서 특정 노트가 열리는
바로가기를 만든다. 사용자는 보통 발표/프로젝트 폴더(예: `My transparencies/2026.10.08 서울대 세미나`)에
그 일과 관련된 Evernote 노트를 같이 두고 싶어 한다.

## 입력

- 노트 링크: `evernote:///view/<userId>/<shard>/<noteGuid>/<notebookGuid 또는 noteGuid>/`
  (Evernote 앱의 "Copy internal link"가 주는 형식. 4번째 요소가 노트북 GUID든 노트 GUID든 둘 다 열린다 — 2026-11-08 확인)
  또는 노트 GUID, 또는 `https://…evernote.com/shard/s28/nl/…` 링크.
- 넣을 폴더. 말 안 하면 현재 작업 폴더.

## 절차

1. **노트 제목 가져오기** — Evernote MCP `get_note(noteId=링크)`로 `title`을 얻는다. MCP가 없으면 사용자에게 제목을 묻는다.
   파일 이름은 `"<제목> (Evernote 노트).app"`. 제목에 `/`나 `:`가 있으면 `-`로 바꾼다.
2. **애플릿 생성** (osacompile, 서명 불필요 — 로컬에서 만든 앱이라 quarantine 없음):
   ```bash
   cd "<폴더>"
   URL='evernote:///view/6010485/s28/<noteGuid>/<notebookGuid>/'
   APP="<제목> (Evernote 노트).app"
   rm -rf "$APP"
   osacompile -o "$APP" -e "open location \"$URL\""
   ```
3. **Evernote 아이콘 입히기** (Finder에서 알아보기 쉽게):
   ```bash
   cp "$(ls /Applications/Evernote.app/Contents/Resources/*.icns | head -1)" "$APP/Contents/Resources/applet.icns"
   touch "$APP"
   ```
   (`Info.plist`의 `CFBundleIconFile`이 `applet`이라 파일만 덮어쓰면 된다.)
4. **동작 확인** — `open "$APP"` 후 4–5초 기다린다. **주의:** Evernote 10의 창 제목은
   `"[D] memo1 (todo) - Evernote"`처럼 노트북 이름만 보여서 제목으로는 확인이 안 된다.
   창 영역을 `screencapture -x -R x,y,w,h`로 찍어(좌표는 System Events의 `position`/`size of window 1`)
   본문 제목이 맞는지 눈으로 확인한다.
5. 작업 폴더 규칙이 있으면(예: 서울대 세미나 폴더는 `claude_session_log_YYYY-MM-DD.md`) 로그에 한 줄 남긴다.

## 하지 말 것 / 알아둘 것

- `.webloc`(plist에 URL 키) 파일은 `open file.webloc`이 `_LSOpenURLsWithCompletionHandler() failed … -10400`으로 실패한다.
  Finder 더블클릭도 보장되지 않으므로 쓰지 않는다. `open "evernote:///…"` 자체는 된다 → 그래서 애플릿으로 감싼다.
- Finder alias는 파일/폴더에만 쓸 수 있고 URL에는 못 쓴다.
- 애플릿은 Dropbox로 동기화되지만 Evernote가 설치된 Mac에서만 동작한다.
- 같은 Mac에서 여러 노트를 넣을 때는 제목이 다르니 이름 충돌이 없지만, 같은 제목이면 `(2)`를 붙인다.

## 예

- 2026-11-08: `evernote:///view/6010485/s28/a3cbe2f3-…/cd070443-…` → "서울대 세미나 준비" →
  `My transparencies/2026.10.08 서울대 세미나/서울대 세미나 준비 (Evernote 노트).app`
