#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
config="$HOME/.config/neuropsi/backup.json"
if [[ ! -f "$config" ]]; then
    echo "Execute python3 infra/backup/backup.py setup primeiro."
    exit 1
fi
# Só instalar o agendamento depois de comprovar uma primeira cópia.
python3 "$root/infra/backup/backup.py" backup
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/neuropsi-backup.service" <<EOF
[Unit]
Description=Backup privado do PostgreSQL Neuropsi Render
[Service]
Type=oneshot
UMask=0077
ExecStart=/usr/bin/python3 "$root/infra/backup/backup.py" backup
TimeoutStartSec=45min
EOF
cat > "$HOME/.config/systemd/user/neuropsi-backup.timer" <<'EOF'
[Unit]
Description=Backup Neuropsi a cada hora
[Timer]
OnCalendar=hourly
Persistent=true
RandomizedDelaySec=60
[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now neuropsi-backup.timer
systemctl --user list-timers neuropsi-backup.timer
