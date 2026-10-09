#!/usr/bin/env bash
# Embedded in a writeShellApplication with an immutable evaluated policy.
set -euo pipefail

case "${1:-}" in
  --sync) sync_mode=1; var_only=0 ;;
  --verify) sync_mode=0; var_only=0 ;;
  --sync-var) sync_mode=1; var_only=1 ;;
  --verify-var) sync_mode=0; var_only=1 ;;
  *) printf 'Usage: granular-final-sync --sync|--verify|--sync-var|--verify-var\n' >&2; exit 2 ;;
esac

if (( EUID != 0 )); then
  printf 'Run as root to preserve ownership, ACLs and xattrs.\n' >&2
  exit 1
fi

# This one-time tool only accepts the live legacy topology. After cutover it
# must refuse to copy reset-root scaffolding over the persistent profiles.
for task_mount in /var /persist; do
  mountpoint -q "$task_mount"
  expected_subvolume="/@${task_mount#/}"
  if [[ "$(findmnt -rn -o FSROOT --mountpoint "$task_mount")" != "$expected_subvolume" ]]; then
    printf 'Refusing migration: %s is not the expected %s mount.\n' "$task_mount" "$expected_subvolume" >&2
    exit 1
  fi
done
if (( var_only )); then
  expected_home=/@root
else
  expected_home=/@home
fi
if [[ "$(findmnt -rn -o FSROOT -T /home)" != "$expected_home" ]]; then
  printf 'Refusing migration: home is not on the expected %s.\n' "$expected_home" >&2
  exit 1
fi

umask 077
evidence=/persist/granular-migration
install -d -m 0700 "$evidence"
task_report=$(mktemp "$evidence/verification.XXXXXX")
trap 'rm -f "$task_report"' EXIT

task_home=$(jq -r .home "$policy")
task_user=$(jq -r .username "$policy")
mapfile -t task_directories < <(jq -r '.directories[]' "$policy")
mapfile -t task_files < <(jq -r '.files[]' "$policy")

mirror_state() {
  local dry_run="$1" task_source task_target
  local -a rsync_flags=(-aHAX --numeric-ids --itemize-changes)
  if (( dry_run )); then rsync_flags+=(-n); fi

  for task_source in "${task_directories[@]}"; do
    if (( var_only )) && [[ "$task_source" != /var/* ]]; then continue; fi
    task_target="/persist$task_source"
    if [[ -d "$task_source" ]] && ! [[ "$task_source" -ef "$task_target" ]]; then
      # Only explicitly declared parents are mirrored. Originals and their
      # immutable migration snapshots are never modified or removed.
      if (( ! dry_run )); then mkdir -p "$task_target"; fi
      rsync "${rsync_flags[@]}" --delete "$task_source/" "$task_target/"
    fi
  done
  for task_source in "${task_files[@]}"; do
    if (( var_only )) && [[ "$task_source" != /var/* ]]; then continue; fi
    task_target="/persist$task_source"
    if [[ -f "$task_source" ]] && ! [[ "$task_source" -ef "$task_target" ]]; then
      if (( ! dry_run )); then mkdir -p "$(dirname "$task_target")"; fi
      rsync "${rsync_flags[@]}" "$task_source" "$task_target"
    fi
  done

  # Preserve existing configuration/history at their new atomic-save locations.
  # Prefer the new locations if the user already started using them.
  if (( ! var_only )) && [[ ! -e "$task_home/.config/git/config" && -f "$task_home/.gitconfig" ]]; then
    if (( ! dry_run )); then
      install -d -m 0700 -o "$task_user" -g users "/persist$task_home/.config/git"
    fi
    rsync "${rsync_flags[@]}" "$task_home/.gitconfig" "/persist$task_home/.config/git/config"
  fi
  if (( ! var_only )) && [[ ! -e "$task_home/.local/state/zsh/history" && -f "$task_home/.config/zsh/.zsh_history" ]]; then
    if (( ! dry_run )); then
      install -d -m 0700 -o "$task_user" -g users "/persist$task_home/.local/state/zsh"
    fi
    rsync "${rsync_flags[@]}" "$task_home/.config/zsh/.zsh_history" "/persist$task_home/.local/state/zsh/history"
  fi
}

if (( sync_mode )); then
  printf 'Final sync started: %s\n' "$(date --iso-8601=seconds)"
  mirror_state 0
  sync -f /persist
fi

mirror_state 1 > "$task_report"
if [[ -s "$task_report" ]]; then
  cat "$task_report"
  printf 'Source changed or backing differs; final sync is not verified.\n' >&2
  exit 1
fi

if (( sync_mode )); then
  date --iso-8601=seconds > "$evidence/final-sync-verified"
  cat /proc/sys/kernel/random/boot_id > "$evidence/final-sync-boot-id"
fi
printf 'Selected state matches the immutable evaluated policy.\n'
