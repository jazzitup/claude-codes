#!/bin/bash
# ~/claude-codes/mac-shortcuts 의 단축키를 이 Mac에 설치한다 (멱등, SessionStart 훅에서 호출됨).
#   Control+Option+Command+S -> qft_layout.sh (Schwartz QFT PDF 두 창 배치)
[ "$(uname)" = Darwin ] || exit 0
HERE="$(cd "$(dirname "$0")" && pwd)"
NAME="QFT 두 창 배치"
KEY='^~@s'                     # ^ = Control, ~ = Option, @ = Command
W="$HOME/Library/Services/$NAME.workflow"
STAMP="$W/Contents/.installed-$(shasum "$0" | cut -c1-12)"
[ -f "$STAMP" ] && exit 0      # 이미 이 버전으로 설치됨

rm -rf "$W"; mkdir -p "$W/Contents"
cat > "$W/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>NSServices</key><array><dict>
<key>NSMenuItem</key><dict><key>default</key><string>$NAME</string></dict>
<key>NSMessage</key><string>runWorkflowAsService</string>
<key>NSRequiredContext</key><dict/>
</dict></array></dict></plist>
PLIST
cat > "$W/Contents/document.wflow" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>AMApplicationBuild</key><string>523</string>
<key>AMApplicationVersion</key><string>2.10</string>
<key>AMDocumentVersion</key><string>2</string>
<key>actions</key><array><dict><key>action</key><dict>
 <key>AMAccepts</key><dict><key>Container</key><string>List</string><key>Optional</key><true/><key>Types</key><array><string>com.apple.cocoa.string</string></array></dict>
 <key>AMActionVersion</key><string>2.0.3</string>
 <key>AMApplication</key><array><string>Automator</string></array>
 <key>AMParameterProperties</key><dict><key>COMMAND_STRING</key><dict/><key>CheckedForUserDefaultShell</key><dict/><key>inputMethod</key><dict/><key>shell</key><dict/><key>source</key><dict/></dict>
 <key>AMProvides</key><dict><key>Container</key><string>List</string><key>Types</key><array><string>com.apple.cocoa.string</string></array></dict>
 <key>ActionBundlePath</key><string>/System/Library/Automator/Run Shell Script.action</string>
 <key>ActionName</key><string>Run Shell Script</string>
 <key>ActionParameters</key><dict>
  <key>COMMAND_STRING</key><string>"$HERE/qft_layout.sh"</string>
  <key>CheckedForUserDefaultShell</key><true/>
  <key>inputMethod</key><integer>0</integer>
  <key>shell</key><string>/bin/bash</string>
  <key>source</key><string></string>
 </dict>
 <key>BundleIdentifier</key><string>com.apple.RunShellScript</string>
 <key>CFBundleVersion</key><string>2.0.3</string>
 <key>CanShowSelectedItemsWhenRun</key><false/>
 <key>CanShowWhenRun</key><true/>
 <key>Category</key><array><string>AMCategoryUtilities</string></array>
 <key>Class Name</key><string>RunShellScriptAction</string>
 <key>InputUUID</key><string>A1B2C3D4-0000-4000-8000-000000000001</string>
 <key>Keywords</key><array><string>Shell</string></array>
 <key>OutputUUID</key><string>A1B2C3D4-0000-4000-8000-000000000002</string>
 <key>UUID</key><string>A1B2C3D4-0000-4000-8000-000000000003</string>
 <key>UnlocalizedApplications</key><array><string>Automator</string></array>
 <key>arguments</key><dict/>
 <key>isViewVisible</key><integer>1</integer>
 <key>location</key><string>309.0:253.0</string>
</dict><key>isViewVisible</key><integer>1</integer></dict></array>
<key>connectors</key><dict/>
<key>workflowMetaData</key><dict>
 <key>serviceInputTypeIdentifier</key><string>com.apple.Automator.nothing</string>
 <key>serviceOutputTypeIdentifier</key><string>com.apple.Automator.nothing</string>
 <key>serviceProcessesInput</key><integer>0</integer>
 <key>workflowTypeIdentifier</key><string>com.apple.Automator.servicesMenu</string>
</dict>
</dict></plist>
PLIST
defaults write pbs NSServicesStatus -dict-add "\"(null) - $NAME - runWorkflowAsService\"" "{ enabled_context_menu = 1; enabled_services_menu = 1; key_equivalent = \"$KEY\"; }"
/System/Library/CoreServices/pbs -flush >/dev/null 2>&1
/System/Library/CoreServices/pbs -update >/dev/null 2>&1
touch "$STAMP"
