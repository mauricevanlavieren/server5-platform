#!/usr/bin/env bash
# Run in the owner's server5 terminal; login URLs remain in that terminal.
set -euo pipefail
umask 077
[[ $(hostname) == server5 && $(id -un) == mau ]] || exit 1
cd /home/mau/server5-commandcenter
python3 - <<'PY'
import json,urllib.request
from pathlib import Path
assert json.loads(Path('inventory/mvp-local-acceptance.json').read_text())['local_real_codex_test']=='passed'
assert json.load(urllib.request.urlopen('http://127.0.0.1:8795/api/health',timeout=5))['status']=='ready'
PY
sudo -v
# Keep LAN DNS and routes; do not enable Tailscale SSH or change netfilter rules.
sudo tailscale up --accept-dns=false --accept-routes=false --ssh=false --netfilter-mode=off
access_status=$(mktemp)
access_serve=$(mktemp)
trap 'rm -f -- "$access_status" "$access_serve"' EXIT
tailscale status --json > "$access_status"
sudo tailscale serve status --json > "$access_serve"
python3 - "$access_status" "$access_serve" <<'PY'
import json,sys
from pathlib import Path
from urllib.parse import urlsplit
status=json.load(open(sys.argv[1]));serve=json.load(open(sys.argv[2]))
assert status['BackendState']=='Running','Tailscale login niet afgerond'
assert not serve or (not serve.get('Web') and not serve.get('TCP') and not serve.get('AllowFunnel')), 'Bestaande Serve-config: eerst beoordelen; niet overschrijven'
name=status['Self']['DNSName'].rstrip('.')
assert name.endswith('.ts.net') and '/' not in name,'Geen bruikbare tailnet-DNS-naam'
origin='https://'+name
Path('/home/mau/.local/state/server5-commandcenter/mvp/public-origin.txt').write_text(origin+'\n')
PY
# Private Serve only. If HTTPS/Serve asks for an account approval URL, review it yourself.
sudo tailscale serve --bg --https=443 http://127.0.0.1:8795
read -r access_host access_ip < <(python3 - "$access_status" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]));print(s['Self']['DNSName'].rstrip('.'),next(ip for ip in s['TailscaleIPs'] if ':' not in ip))
PY
)
curl --noproxy '*' --resolve "$access_host:443:$access_ip" --retry 3 --retry-connrefused -fsS "https://$access_host/api/health" >/dev/null
python3 - "$access_host" <<'PY'
import json,sys,time
from pathlib import Path
origin='https://'+sys.argv[1]
Path('inventory/mvp-private-acceptance.json').write_text(json.dumps({'origin':origin,'https_health':'passed','at':time.time()}))
print('Private HTTPS lokaal getest:',origin)
print('Open dit adres op je telefoon met Tailscale aan, op hetzelfde tailnet.')
print('Toegangscode tonen in eigen terminal: python3 web/commandcenter.py password')
print('Meld daarna verbinding gereed aan Codex; deel geen toegangscode of loginlink.')
PY
