#!/bin/bash
# iTerm2: 한글 입력 상태에서도 Ctrl+A / Ctrl+E 가 동작하게 한다 (멱등, SessionStart 훅에서 호출됨).
# 한글 자판에선 Ctrl+A 가 Ctrl+ㅁ 이 되어 제어문자가 안 나간다 -> 물리 키(keycode)로 매칭하는
# GlobalKeyMap 항목을 넣어 직접 hex 코드를 보낸다. 키 형식: "<char>-<mods>-<keycode>-0x1".
# 주의: 값은 반드시 XML(<integer>) 로 써야 한다. '{Action = 11;}' 식으로 쓰면 문자열로 저장돼
#       키를 누를 때 iTerm2 가 크래시한다 (2026-10-27 실제로 겪음).
# 반영은 iTerm2 를 재시작(⌘Q)한 뒤부터.
[ "$(uname)" = Darwin ] || exit 0
[ -d /Applications/iTerm.app ] || exit 0
D=com.googlecode.iterm2

# 키 이름  key                     보낼 hex
BINDINGS="
ctrl-a   0x61-0x40000-0x0-0x1    0x01
ctrl-e   0x65-0x40000-0xe-0x1    0x05
"

defaults write $D LanguageAgnosticKeyBindings -bool true
# 새 Mac 이라 GlobalKeyMap 이 아직 없으면, 우리 항목만 넣으면 iTerm2 기본 단축키가 사라진다
# -> 앱에 들어있는 기본 키맵으로 먼저 채운다.
if ! defaults read $D GlobalKeyMap >/dev/null 2>&1; then
    DEF=/Applications/iTerm.app/Contents/Resources/DefaultGlobalKeyMap.plist
    [ -f "$DEF" ] || exit 0
    defaults write $D GlobalKeyMap "$(plutil -convert xml1 -o - "$DEF" | sed '1,3d;$d')"
fi
echo "$BINDINGS" | while read -r _ key hex; do
    [ -n "$key" ] || continue
    # 이미 정수 타입으로 제대로 들어가 있으면 건너뜀
    cur=$(defaults export $D - 2>/dev/null | plutil -extract "GlobalKeyMap.$key" xml1 -o - - 2>/dev/null)
    echo "$cur" | grep -q "<integer>11</integer>" && echo "$cur" | grep -q "<string>$hex</string>" && continue
    defaults write $D GlobalKeyMap -dict-add "$key" \
        "<dict><key>Action</key><integer>11</integer><key>Apply Mode</key><integer>0</integer><key>Escaping</key><integer>2</integer><key>Text</key><string>$hex</string><key>Version</key><integer>2</integer></dict>"
done
exit 0
