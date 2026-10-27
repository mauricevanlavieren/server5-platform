#!/usr/bin/env bash
set -euo pipefail
if [[ "$(hostname)" != server5 ]]; then
  echo 'Start deze bestaande demo-route uitsluitend op Server5.' >&2
  exit 1
fi
systemctl --user start server5-demo-forward.service
exec /usr/local/bin/ngrok http http://127.0.0.1:8874 --url=https://prognosis-energize-calzone.ngrok-free.dev --inspect=false --traffic-policy-file=/home/mau/server5-commandcenter/config/ngrok-demo-policy.json
