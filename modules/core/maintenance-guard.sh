#!/usr/bin/env bash
# ExecCondition: skip rather than fail the unit when storage state is unsafe.
set -u
export LC_ALL=C
mode=$1
systemctl_command=$2
btrfs_command=$3

case "$mode" in
  gc) peer=btrfs-scrub--.service ;;
  scrub) peer=nix-gc.service ;;
  *) exit 1 ;;
esac

if ! state=$("$systemctl_command" show "$peer" -p ActiveState --value); then
  echo 'Skipping maintenance: cannot inspect peer service.'
  exit 1
fi
case "$state" in
  inactive) ;;
  failed) if [[ "$mode" == gc ]]; then exit 1; fi ;;
  *) echo "Skipping maintenance: $peer state is $state."; exit 1 ;;
esac

if [[ "$mode" == gc ]]; then
  if ! report=$("$btrfs_command" scrub status /); then
    echo 'Skipping GC: scrub status unavailable.'
    exit 1
  fi
  finished=false
  clean=false
  while IFS= read -r line; do
    case "$line" in
      Status:*)
        case "$line" in
          *finished*) finished=true ;;
          *) echo 'Skipping GC: scrub has not finished.'; exit 1 ;;
        esac
        ;;
      'Error summary:'*)
        case "$line" in
          *'no errors found'*) clean=true ;;
          *) echo 'Skipping GC: scrub reports errors or unknown health.'; exit 1 ;;
        esac
        ;;
    esac
  done <<< "$report"
  if ! $finished || ! $clean; then
    echo 'Skipping GC: no completed clean scrub evidence.'
    exit 1
  fi
fi
