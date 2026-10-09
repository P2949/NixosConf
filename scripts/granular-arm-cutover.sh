#!/usr/bin/env bash
# Install an already validated closure for boot, retaining the old default.
set -euo pipefail
if (( EUID != 0 )) || [[ $# != 2 ]]; then
  printf 'Usage (root): granular-arm-cutover home|var SYSTEM\n' >&2
  exit 2
fi
task_phase=$1
task_system=$(readlink -f "$2")
case "$task_phase" in home|var) ;; *) exit 2 ;; esac
[[ "$task_system" == /nix/store/* && -x "$task_system/bin/switch-to-configuration" ]]
[[ ! -e /persist/granular-migration/physical-boot-pending.json ]]
if systemctl is-active --quiet granular-final-copy.service; then
  printf 'The final-copy service is already armed.\n' >&2
  exit 1
fi
[[ "$(findmnt -rn -o FSROOT --mountpoint /var)" == /@var ]]
if [[ "$task_phase" == home ]]; then task_home=/@home; else task_home=/@root; fi
[[ "$(findmnt -rn -o FSROOT -T /home)" == "$task_home" ]]
[[ "$(findmnt -rn -o FSROOT --mountpoint /persist)" == /@persist ]]
if [[ "$task_phase" == var ]]; then
  "$home_acceptance/bin/granular-home-acceptance"
fi

umask 077
task_evidence=/persist/granular-migration
install -d -m 0700 "$task_evidence"
task_current=$(readlink -f /run/current-system)
entry_for_system() {
  bootctl list --json=short | jq -er --arg task_init "init=$1/init" \
    '[.[] | select(.options != null) | select(.options | split(" ") | index($task_init)) | .id][0]'
}
task_rollback=$(entry_for_system "$task_current")
printf '%s\n' "$task_current" > "$task_evidence/pre-cutover-system"
printf '%s\n' "$task_rollback" > "$task_evidence/pre-cutover-boot-entry"

# EFI's default overrides loader.conf. Keep it pinned to the known current
# generation during installation, and on every preparation error afterward.
bootctl set-default "$task_rollback"
trap 'bootctl set-default "$task_rollback"' ERR
nixos-rebuild boot --no-reexec --store-path "$task_system"
bootctl set-default "$task_rollback"
task_entry=$(entry_for_system "$task_system")
[[ "$task_entry" =~ ^[A-Za-z0-9._-]+\.conf$ ]]
[[ "$(readlink -f /run/current-system)" == "$task_current" ]]
task_scopes=$(systemctl list-units 'session-*.scope' --no-legend --plain --all --no-pager | awk '{print $1}' | tr '\n' ' ')

cat > "$task_evidence/granular-final-copy.service" <<EOF
[Unit]
Description=Verified granular Impermanence final copy and one-shot cutover
DefaultDependencies=no
RequiresMountsFor=/home /var /persist /boot /nix
After=local-fs.target
Before=shutdown.target user@$desktop_uid.service user-runtime-dir@$desktop_uid.service greetd.service NetworkManager.service bluetooth.service systemd-random-seed.service nix-daemon.service nix-daemon.socket $task_scopes
Conflicts=shutdown.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=$coreutils/bin/true
ExecStop=$shutdown_cutover/bin/granular-shutdown-cutover $task_phase $task_system $task_entry
TimeoutStopSec=30min
StandardOutput=append:$task_evidence/final-copy-shutdown.log
StandardError=append:$task_evidence/final-copy-shutdown.log
EOF
install -m 0600 /dev/null "$task_evidence/final-copy-shutdown.log"
install -m 0644 "$task_evidence/granular-final-copy.service" /run/systemd/system/granular-final-copy.service
systemd-analyze verify /run/systemd/system/granular-final-copy.service
systemctl daemon-reload
systemctl start granular-final-copy.service
systemctl is-active --quiet granular-final-copy.service
printf '%s\n' "$task_system" > "$task_evidence/armed-cutover-system"
printf '%s\n' "$task_entry" > "$task_evidence/armed-cutover-boot-entry"
printf 'Armed %s cutover for the next orderly shutdown. No reboot requested.\n' "$task_phase"
printf 'Rollback default: %s; candidate one-shot after verified copy: %s\n' "$task_rollback" "$task_entry"
