# Keynote: Shift+Command+R → 선택 객체에 Build In "Dissolve" 넣기

Keynote에는 "Build In > Dissolve"에 해당하는 메뉴 항목이 없어서 시스템 설정의
키보드 단축키로는 못 만든다. 그래서 **Automator Quick Action(서비스) + System Events
UI 스크립팅**으로 인스펙터를 대신 눌러 주는 방식으로 만들었다 (2026-11-07).

## 사용법

1. Keynote에서 슬라이드의 객체(그림, 텍스트 상자, 도형 …)를 선택한다. 여러 개 선택도 됨.
2. **Shift+Command+R**.
3. 오른쪽 Animate 인스펙터가 열리고 Build In 탭에 Dissolve가 들어간다
   (이미 효과가 있으면 Dissolve로 바뀐다).
- 객체를 선택하지 않고 누르면 "슬라이드에서 객체를 먼저 선택하세요" 알림만 뜬다.

## 파일

| 파일 | 역할 |
|---|---|
| `mac-shortcuts/keynote_dissolve_buildin.sh` | 실제 동작(AppleScript 내장). 로그: `~/Library/Logs/keynote_dissolve_buildin.log` |
| `mac-shortcuts/install.sh` | `~/Library/Services/Keynote Dissolve 빌드인.workflow` 생성 + `pbs NSServicesStatus`에 `$@r`(Shift+Cmd+R) 바인딩. 멱등. |
| `scripts/session-start-setup.sh` | Claude Code 세션 시작마다 `install.sh`를 호출 → 자동 설치 |

동작 순서(스크립트 안): 툴바의 **Animate** 세그먼트 클릭(툴바가 숨겨져 있으면 View > Inspector > Animate)
→ 인스펙터의 **Build In** 세그먼트 → **Add an Effect**(또는 **Change**) 버튼 → 팝오버에서 **Dissolve** 버튼.
영어/한국어 UI 레이블 둘 다 찾도록 돼 있다. 프로세스 이름은 앱 이름이 "Keynote Creator Studio"여도 `Keynote`다.

## 다른 Mac에서 쓰려면

1. `~/claude-codes`를 `git pull` (이 저장소는 모든 Mac에 같은 경로로 clone돼 있어야 한다).
2. Claude Code 세션을 한 번 열면 SessionStart 훅이 `install.sh`를 돌려 서비스가 설치된다.
   바로 쓰고 싶으면 터미널에서 직접:
   ```bash
   ~/claude-codes/mac-shortcuts/install.sh
   ```
3. **손쉬운 사용(Accessibility) 권한** — UI 스크립팅이라 처음 한 번은 필요하다.
   Keynote에서 Shift+Cmd+R을 눌렀을 때 아무 일도 없거나 권한 대화상자가 뜨면:
   시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용 에서 **WorkflowServiceRunner**
   (없으면 `+`로 `/System/Library/CoreServices/WorkflowServiceRunner.app` 추가; 간혹 `osascript`)를 켠다.
   `~/Library/Logs/keynote_dissolve_buildin.log`에 `ok`가 찍히면 정상.
4. 키가 안 먹으면 pbs 캐시 갱신: `/System/Library/CoreServices/pbs -flush; /System/Library/CoreServices/pbs -update`
   그래도 안 되면 로그아웃/로그인. 시스템 설정 > 키보드 > 키보드 단축키 > 서비스 > 일반 에
   "Keynote Dissolve 빌드인"이 ⇧⌘R로 보이면 등록된 것.

## 고치기 / 다른 효과로 바꾸기

- 다른 효과(예: "Fade and Move", "Appear")로 바꾸려면 `keynote_dissolve_buildin.sh`의
  `{"Dissolve", "디졸브"}` 부분을 바꾼다. 팝오버 버튼 이름은 Keynote 인스펙터에 보이는 영어 이름 그대로.
- Build Out용을 만들려면 `{"Build In", "빌드 인", "나타나기"}` 를 `{"Build Out", ...}`로.
- 스크립트를 고친 뒤 `install.sh`는 파일 해시가 바뀌면 자동으로 다시 설치한다(세션 시작 또는 직접 실행).
- 디버깅: `bash ~/claude-codes/mac-shortcuts/keynote_dissolve_buildin.sh; tail ~/Library/Logs/keynote_dissolve_buildin.log`
  (객체를 선택한 상태로 Keynote를 띄워 두고 실행).

## 검증 기록

- 2026-11-07, macOS 26.6.2, Keynote 14.5(Keynote Creator Studio) 영어 UI: 새 문서에 텍스트 상자 만들고 ⌘A 후
  스크립트 실행 → 인스펙터에 Build In / Dissolve / Change 버튼 확인. Keynote 자체 단축키와 충돌 없음
  (⌘R은 Show Rulers, ⇧⌘R은 비어 있음).
