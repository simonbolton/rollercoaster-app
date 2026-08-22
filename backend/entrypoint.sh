#!/bin/sh
set -eu

python /app/backend/server.py &
server_pid=$!

if [ "${SYNC_ON_START:-true}" = "true" ]; then
  python /app/backend/sync_wikidata.py || echo "Wikidata refresh unavailable; using existing data"
fi

wait "$server_pid"
