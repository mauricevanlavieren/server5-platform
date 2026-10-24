#!/usr/bin/env bash
# Run as mau in your own server5 terminal. No password is sent to the agent.
set -euo pipefail
[[ $(hostname) == server5 && $(id -un) == mau ]] || exit 1
source /etc/os-release
[[ $VERSION_CODENAME == noble ]] || { echo 'Expected Ubuntu noble'; exit 1; }
sudo -v
if ! command -v tailscale >/dev/null; then
  key=/usr/share/keyrings/tailscale-archive-keyring.gpg
  source_list=/etc/apt/sources.list.d/tailscale.list
  [[ ! -e $key && ! -e $source_list ]] || { echo 'Existing Tailscale APT files: stop for review'; exit 1; }
  access_tmp=$(mktemp -d)
  trap 'rm -rf -- "$access_tmp"' EXIT
  curl --proto '=https' --tlsv1.2 -fsS https://pkgs.tailscale.com/stable/ubuntu/noble.noarmor.gpg -o "$access_tmp/key.gpg"
  curl --proto '=https' --tlsv1.2 -fsS https://pkgs.tailscale.com/stable/ubuntu/noble.tailscale-keyring.list -o "$access_tmp/tailscale.list"
  grep -q 'signed-by=/usr/share/keyrings/tailscale-archive-keyring.gpg' "$access_tmp/tailscale.list"
  sudo -n install -o root -g root -m 0644 "$access_tmp/key.gpg" "$key"
  sudo -n install -o root -g root -m 0644 "$access_tmp/tailscale.list" "$source_list"
  sudo -n apt-get update
  sudo -n apt-get --simulate --no-remove --no-upgrade --no-install-recommends install tailscale
  sudo -n apt-get --no-remove --no-upgrade --no-install-recommends install tailscale
fi
sudo -n loginctl enable-linger mau
printf '%s\n' 'Tailscale installed; user services can start before login. No tailscale up/serve run.'
printf '%s\n' 'Tell Codex: installatie gereed. Do not paste credentials.'
