#!/bin/bash
# Shift+Command+R (Keynote): 선택한 객체에 Animate > Build In > Dissolve 효과를 넣는다.
#   실제 동작은 keynote_dissolve_buildin.applescript (System Events UI 스크립팅).
#   손쉬운 사용(Accessibility) 권한을 Automator 실행기(XPC)가 아니라 전용 applet 하나에만 주면 되도록,
#   이 스크립트는 .applescript 를 "Keynote Dissolve.app" 으로 컴파일해 두고(소스가 바뀌면 다시) 그 앱을 연다.
#   처음 실행 때 "Keynote Dissolve 가 손쉬운 사용 기능으로 이 컴퓨터를 제어하려고 합니다" 창이 뜨면 허용 → 그 뒤로는 바로 동작.
#   (applet 을 다시 컴파일하면 권한을 다시 켜야 할 수 있다.)
[ "$(uname)" = Darwin ] || exit 0
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/keynote_dissolve_buildin.applescript"
APPDIR="$HOME/Library/Application Support/claude-codes"
APP="$APPDIR/Keynote Dissolve.app"
STAMP="$APP/Contents/Resources/.src-$(shasum "$SRC" | cut -c1-12)"
if [ ! -f "$STAMP" ]; then
  mkdir -p "$APPDIR"; rm -rf "$APP"
  /usr/bin/osacompile -o "$APP" "$SRC" || exit 1
  # Dock 에 안 뜨게 + 고정 bundle id
  /usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$APP/Contents/Info.plist" >/dev/null 2>&1
  /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.yongsunkim.keynote-dissolve" "$APP/Contents/Info.plist" >/dev/null 2>&1
  /usr/bin/codesign --force --sign - --identifier com.yongsunkim.keynote-dissolve "$APP" >/dev/null 2>&1
  touch "$STAMP"
fi
exec /usr/bin/open -a "$APP"
