#!/usr/bin/env bash
# Run only by the reviewed shutdown unit after user and stateful services stop.
set -euo pipefail

if (( EUID != 0 )) || [[ $# != 3 ]]; then
  printf 'Usage (root): granular-shutdown-cutover home|var SYSTEM BOOT_ENTRY\n' >&2
  exit 2
fi
task_phase=$1
task_system=$2
task_entry=$3
case "$task_phase" in
  home) task_sync=--sync; task_check=home ;;
  var) task_sync=--sync-var; task_check=normal ;;
  *) exit 2 ;;
esac
[[ "$task_system" == /nix/store/* && -x "$task_system/bin/switch-to-configuration" ]]
[[ "$task_entry" =~ ^[A-Za-z0-9._-]+\.conf$ ]]
grep -Fq "init=$task_system/init " "/boot/loader/entries/$task_entry"

# Refuse the cutover if any process of the desktop user remains alive. An
# unsuccessful final sync leaves the old boot default and originals intact.
if pgrep -u "$desktop_uid" > /dev/null; then
  printf 'Desktop processes still running; retaining the old boot default.\n' >&2
  exit 1
fi
"$physical_check/bin/granular-physical-check" seed "$task_check" "$task_system"
"$final_sync/bin/granular-final-sync" "$task_sync"
bootctl set-oneshot "$task_entry"
sync -f /boot
printf 'Quiesced copy verified; selected %s for one boot.\n' "$task_entry"
