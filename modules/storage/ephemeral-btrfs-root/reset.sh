# shellcheck shell=bash
# shellcheck disable=SC2154
set -euo pipefail

# Configuration is provided as escaped assignments and an array by Nix.
# shellcheck disable=SC2154
root="$top/$root_name"
next="$top/$next_name"
persist="$top/$persist_name"

if mountpoint -q /sysroot; then
  echo "FAIL: refusing Btrfs root reset because /sysroot is already mounted" >&2
  exit 1
fi

mkdir -p "$top"

cleanup() {
  if mountpoint -q "$top"; then
    umount "$top"
  fi
}

trap cleanup EXIT

mount \
  -t btrfs \
  -o subvolid=5 \
  "$root_device" \
  "$top"

if [[ ! -e "$persist" ]]; then
  echo "FAIL: persistence subvolume is missing: $persist" >&2
  exit 1
fi

if [[ -L "$persist" ]] || ! btrfs subvolume show "$persist" >/dev/null 2>&1; then
  echo "FAIL: persistence path is not a Btrfs subvolume: $persist" >&2
  exit 1
fi

log_file="$persist/$log_relative"

# Never follow an alias while creating diagnostics: otherwise even a
# refused reset could chmod or append to unrelated persistent data.
log_parent="$persist"
IFS=/ read -r -a log_parts <<< "$log_relative"
for ((i = 0; i < ${#log_parts[@]} - 1; i++)); do
  log_parent="$log_parent/${log_parts[i]}"
  if [[ -L "$log_parent" ]] || [[ -e "$log_parent" && ! -d "$log_parent" ]]; then
    echo "FAIL: unsafe reset log parent: $log_parent" >&2
    exit 1
  fi
  if [[ ! -e "$log_parent" ]]; then
    mkdir "$log_parent"
  fi
done
if [[ -L "$log_file" ]] || [[ -e "$log_file" && ! -f "$log_file" ]]; then
  echo "FAIL: reset log must be a regular file without aliases" >&2
  exit 1
fi
if [[ -e "$log_file" && "$(stat -c %h "$log_file")" != 1 ]]; then
  echo "FAIL: reset log must not have hard links" >&2
  exit 1
fi
touch "$log_file"
chmod 0600 "$log_file"

log() {
  local message="$*"

  printf \
    '[%s] %s\n' \
    "$(date --iso-8601=seconds)" \
    "$message" \
    | tee -a "$log_file" >&2
}

show_subvolume() {
  local label="$1"
  local path="$2"

  log "$label"

  btrfs subvolume show "$path" \
    2>&1 \
    | tee -a "$log_file" >&2
}

require_no_descendants() {
  local path="$1"
  local label="$2"
  local output

  output="$(btrfs subvolume list -o "$path")"

  if [[ -n "$output" ]]; then
    log "FAIL: $label contains unexpected descendants"

    printf '%s\n' "$output" \
      | tee -a "$log_file" >&2

    return 1
  fi
}

require_empty_staging() {
  local path="$1"
  local label="$2"
  local entries

  require_no_descendants "$path" "$label"

  # Include dotfiles and broken symlinks; an interrupted reset only
  # leaves a genuinely empty staging subvolume.
  shopt -s nullglob dotglob
  entries=("$path"/*)
  shopt -u nullglob dotglob

  if (( ${#entries[@]} != 0 )); then
    log "FAIL: $label contains unexpected directory entries"
    return 1
  fi
}

boot_id="$(
  cat /proc/sys/kernel/random/boot_id \
    2>/dev/null \
    || printf '%s' unknown
)"

log "BEGIN boot_id=$boot_id device=$root_device"
log "top-level Btrfs mount established"

if [[ ! -e "$root" && ! -L "$root" ]]; then
  if [[ ! -e "$next" && ! -L "$next" ]]; then
    log "FAIL: neither $root_name nor $next_name exists"
    exit 1
  fi

  if [[ -L "$next" ]] || ! btrfs subvolume show "$next" >/dev/null 2>&1; then
    log "FAIL: $next_name exists but is not a Btrfs subvolume"
    exit 1
  fi

  require_empty_staging \
    "$next" \
    "$next_name"

  show_subvolume \
    "recoverable staging subvolume:" \
    "$next"

  log "recovering interrupted reset: $next_name -> $root_name"

  mv "$next" "$root"
  sync

  show_subvolume \
    "recovered root subvolume:" \
    "$root"

  log "RECOVERY complete"
  sync

  exit 0
fi

if [[ -L "$root" ]] || ! btrfs subvolume show "$root" >/dev/null 2>&1; then
  log "FAIL: $root_name exists but is not a Btrfs subvolume"
  exit 1
fi

show_subvolume \
  "root before reset:" \
  "$root"

if [[ -e "$next" || -L "$next" ]]; then
  if [[ -L "$next" ]] || ! btrfs subvolume show "$next" >/dev/null 2>&1; then
    log "FAIL: $next_name exists but is not a Btrfs subvolume"
    exit 1
  fi

  require_empty_staging \
    "$next" \
    "$next_name"
fi

is_allowed_descendant() {
  local candidate=$1
  local allowed
  for allowed in "${allowed_descendants[@]}"; do
    if [[ "$candidate" == "$root_name/$allowed" ]]; then
      return 0
    fi
  done
  return 1
}

root_descendants=()
descendant_output="$(btrfs subvolume list -o "$root")"

if [[ -n "$descendant_output" ]]; then
  while IFS= read -r line; do
    if [[ "$line" != *" path "* ]]; then
      log "FAIL: could not parse descendant line: $line"
      exit 1
    fi

    candidate="${line#* path }"

    if ! is_allowed_descendant "$candidate"; then
      log "FAIL: refusing to delete unknown root descendant: $candidate"
      exit 1
    fi

    # The root-level list may only expose direct children. Every
    # allowed child must itself have no nested subvolumes.
    require_no_descendants "$top/$candidate" "$candidate"

    root_descendants+=("$candidate")
  done <<< "$descendant_output"
fi

if (( ${#root_descendants[@]} == 0 )); then
  log "root descendant audit passed: none present"
else
  for candidate in "${root_descendants[@]}"; do
    log "root descendant audit passed: $candidate"
  done
fi

# All topology checks must pass before the first destructive action.
if [[ -e "$next" ]]; then
  log "deleting stale empty staging subvolume $next_name"

  btrfs subvolume delete \
    -c \
    "$next"
fi

log "creating empty staging subvolume $next_name"

btrfs subvolume create "$next"
sync

for candidate in "${root_descendants[@]}"; do
  log "deleting validated disposable descendant: $candidate"

  btrfs subvolume delete \
    -c \
    "$top/$candidate"
done

log "deleting old root subvolume non-recursively"

btrfs subvolume delete \
  -c \
  "$root"

log "renaming $next_name -> $root_name"

mv "$next" "$root"

show_subvolume \
  "new root subvolume:" \
  "$root"

log "RESET complete"

sync
