#!/usr/bin/env bash
set -euo pipefail
[[ $(hostname) == server5 ]] || exit 1
cd /home/mau/server5-commandcenter
python3 -m unittest discover -s tests -v
bash -n scripts/prepare-security.sh
systemd-analyze --user verify systemd/user/*
git diff --check
python3 scripts/commandcenter.py status
systemctl --user is-enabled server5-health.timer server5-backup.timer
systemctl --user is-active server5-health.timer server5-backup.timer
systemctl --user show server5-health.service server5-backup.service -p Result -p ExecMainStatus
loginctl show-user mau -p Linger
