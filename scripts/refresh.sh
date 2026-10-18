#!/bin/bash
# Copies your newest Claude Code + Cowork chats, restarts the viewer, rebuilds the library page.
# Your originals are only read, never changed. Add --open to open the page when done.
set -euo pipefail
. "$(dirname "$0")/_env.sh"
A="$DATA/projects"; C="$HOME/Library/Application Support/Claude/local-agent-mode-sessions"
mkdir -p "$A"
echo "[$(date '+%F %T')] copying chats"
[ -d "$HOME/.claude/projects" ] && rsync -a --prune-empty-dirs --include='*/' --include='*.jsonl' --exclude='*' "$HOME/.claude/projects/" "$A/"
if [ -d "$C" ]; then
  find "$C" -maxdepth 7 -type d -path '*/.claude/projects/-*' -print0 2>/dev/null | while IFS= read -r -d '' p; do
    rsync -a --prune-empty-dirs --include='*/' --include='*.jsonl' --exclude='*' "$p/" "$A/$(basename "$p")/"
  done
fi
echo "[$(date '+%F %T')] restarting viewer"
if launchctl print "gui/$UIDN/$LABEL_SERVER" >/dev/null 2>&1; then
  : > "$DATA/viewer.log"
  launchctl kickstart -k "gui/$UIDN/$LABEL_SERVER"
else
  pkill -f "claude-code-log serve" 2>/dev/null || true; sleep 1
  nohup bash "$CODE/scripts/run-viewer.sh" > "$DATA/viewer.log" 2>&1 &
fi
for _ in $(seq 1 150); do grep -q "Serving" "$DATA/viewer.log" 2>/dev/null && break; sleep 2; done
grep -q "Serving" "$DATA/viewer.log" || { echo "viewer did not start, see $DATA/viewer.log"; exit 1; }
echo "[$(date '+%F %T')] building library"
CHAT_LIBRARY_HOME="$DATA" /usr/bin/python3 -I "$CODE/tools/build_library.py" | head -3
echo "done: $URL"
[ "${1:-}" = "--open" ] && open "$URL" || true
