#!/bin/bash
# Stops the viewer and the weekly refresh. Your chat archive is NOT deleted.
. "$(dirname "$0")/_env.sh"
for L in "$LABEL_SERVER" "$LABEL_WEEKLY"; do
  launchctl bootout "gui/$UIDN/$L" 2>/dev/null || true
  rm -f "$HOME/Library/LaunchAgents/$L.plist"
done
pkill -f "claude-code-log serve" 2>/dev/null || true
echo "Stopped. Your archive is still at: $DATA (delete that folder yourself if you want it gone)."
