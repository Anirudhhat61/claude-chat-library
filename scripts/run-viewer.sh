#!/bin/bash
# Serves your chat archive on this computer only (127.0.0.1), inside a macOS sandbox that
# blocks all outbound network traffic except loopback. The viewer cannot send anything out.
set -e
. "$(dirname "$0")/_env.sh"
mkdir -p "$DATA/projects"
exec /usr/bin/sandbox-exec -p '(version 1)
(allow default)
(deny network-outbound)
(allow network-outbound (remote ip "localhost:*"))
(allow network-inbound (local ip "localhost:*"))
(allow network-bind (local ip "localhost:*"))' \
  "$CLV" serve --projects-dir "$DATA/projects" --port "$PORT"
