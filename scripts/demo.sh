#!/bin/bash
# Try Chat Library with invented sample chats. No personal data, nothing installed at login.
# Opens http://127.0.0.1:8011/library.html. Stop it with:  pkill -f chat-library-demo
set -euo pipefail
. "$(dirname "$0")/_env.sh"
command -v uv >/dev/null 2>&1 || { echo "Install the 'uv' tool first:  brew install uv"; exit 1; }
[ -x "$CLV" ] || uv tool install claude-code-log==1.7.0 >/dev/null
DEMO="${TMPDIR:-/tmp}/chat-library-demo"; DPORT=8011
pkill -f "chat-library-demo" 2>/dev/null || true; sleep 1
rm -rf "$DEMO"; mkdir -p "$DEMO"
/usr/bin/python3 -I "$CODE/tools/make_demo.py" "$DEMO"
nohup "$CLV" serve --projects-dir "$DEMO/projects" --port "$DPORT" > "$DEMO/viewer.log" 2>&1 &
for _ in $(seq 1 60); do grep -q "Serving" "$DEMO/viewer.log" 2>/dev/null && break; sleep 1; done
grep -q "Serving" "$DEMO/viewer.log" || { echo "viewer did not start, see $DEMO/viewer.log"; exit 1; }
CHAT_LIBRARY_HOME="$DEMO" /usr/bin/python3 -I "$CODE/tools/build_library.py" | head -1
echo "Open: http://127.0.0.1:$DPORT/library.html   (stop with: pkill -f chat-library-demo)"
[ "${1:-}" = "--no-open" ] || open "http://127.0.0.1:$DPORT/library.html"
