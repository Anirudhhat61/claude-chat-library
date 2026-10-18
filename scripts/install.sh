#!/bin/bash
# One-time setup (macOS). Installs the viewer, starts it at login, and refreshes it every Monday 7:00.
set -euo pipefail
. "$(dirname "$0")/_env.sh"
[ "$(uname)" = "Darwin" ] || { echo "This kit is macOS only."; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "Install the 'uv' tool first:  brew install uv"; exit 1; }
[ -d "$HOME/.claude/projects" ] || echo "Note: no Claude Code chats found yet at ~/.claude/projects (Cowork chats are still picked up)."
echo "Installing claude-code-log 1.7.0 (pinned)"
uv tool install --force claude-code-log==1.7.0 >/dev/null
chmod +x "$CODE"/scripts/*.sh
mkdir -p "$DATA/projects" "$HOME/Library/LaunchAgents"
PL="$HOME/Library/LaunchAgents"
ENVX="<key>EnvironmentVariables</key><dict><key>CHAT_LIBRARY_HOME</key><string>$DATA</string><key>CHAT_LIBRARY_PORT</key><string>$PORT</string><key>PATH</key><string>$HOME/.local/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string></dict>"
cat > "$PL/$LABEL_SERVER.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>$LABEL_SERVER</string>
<key>ProgramArguments</key><array><string>/bin/bash</string><string>$CODE/scripts/run-viewer.sh</string></array>
<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
$ENVX
<key>StandardOutPath</key><string>$DATA/viewer.log</string><key>StandardErrorPath</key><string>$DATA/viewer.log</string>
</dict></plist>
PLIST
cat > "$PL/$LABEL_WEEKLY.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>$LABEL_WEEKLY</string>
<key>ProgramArguments</key><array><string>/bin/bash</string><string>$CODE/scripts/refresh.sh</string></array>
<key>StartCalendarInterval</key><dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
$ENVX
<key>StandardOutPath</key><string>$DATA/weekly.log</string><key>StandardErrorPath</key><string>$DATA/weekly.log</string>
</dict></plist>
PLIST
pkill -f "claude-code-log serve" 2>/dev/null || true
for L in "$LABEL_SERVER" "$LABEL_WEEKLY"; do
  launchctl bootout "gui/$UIDN/$L" 2>/dev/null || true
  launchctl bootstrap "gui/$UIDN" "$PL/$L.plist"
done
echo "Building the library (takes about a minute)"
bash "$CODE/scripts/refresh.sh"
echo
echo "Ready. Bookmark this:  $URL"
echo "It refreshes itself every Monday at 7:00 (a Mac that was asleep catches up when it wakes)."
