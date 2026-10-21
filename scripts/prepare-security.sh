#!/usr/bin/env bash
# User runs this in their own terminal. Never enter a password in chat.
set -euo pipefail
[[ $(hostname) == server5 ]] || { echo 'Verkeerde host'; exit 1; }
[[ $(id -u) != 0 ]] || { echo 'Start als mau, niet als root'; exit 1; }
[[ $(id -un) == mau ]] || exit 1
sudo -v
printf '%s\n' 'Installatieplan: uitsluitend bubblewrap; geen verwijderingen.'
sudo -n apt-get --simulate install bubblewrap
sudo -n apt-get --no-remove install bubblewrap
printf '%s\n' 'SSH-configuratie alleen valideren; geen reload.'
sudo -n /usr/sbin/sshd -t
printf '%s\n' 'AppArmor-status alleen lezen.'
sudo -n aa-status
printf '%s\n' 'Bubblewraptest als gewone gebruiker:'
bwrap --ro-bind / / --unshare-user --unshare-pid --proc /proc --dev /dev /bin/true
printf '%s\n' 'Basiscontrole geslaagd; meld gereed aan Codex.'
