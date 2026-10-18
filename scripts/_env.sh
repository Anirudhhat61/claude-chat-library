# Shared settings. Override with environment variables if you must.
CODE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="${CHAT_LIBRARY_HOME:-$HOME/Documents/Claude-Chat-Viewer}"
PORT="${CHAT_LIBRARY_PORT:-8010}"
CLV="$HOME/.local/bin/claude-code-log"
LABEL_SERVER="local.chatlibrary.server"
LABEL_WEEKLY="local.chatlibrary.weekly"
URL="http://127.0.0.1:$PORT/library.html"
UIDN="$(id -u)"
