#!/usr/bin/env bash
# Read-only stock-workstation snapshot. Run from the repository root.
set -u
export LC_ALL=C
unset LD_LIBRARY_PATH

capture() {
  local label=$1
  shift
  printf '\n## %s\n\n```text\n' "$label"
  timeout --signal=TERM --kill-after=5s 45s "$@" 2>&1
  local status=$?
  printf '\n[exit=%s]\n```\n' "$status"
}

capture_privileged() {
  local label=$1
  shift
  if (( EUID == 0 )); then
    capture "$label" "$@"
  else
    capture "$label" sudo -n "$@"
  fi
}

printf '# Workstation state snapshot\n\n'
printf 'Captured: %s\n\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
printf 'This is observed runtime state, not final acceptance or an idle/load test.\n'
capture 'Git identity' git log -1 --format='%H %s'
capture 'Git tags' git tag --points-at HEAD
capture 'Working tree' git status --short
capture 'Collector source identity' sha256sum "${BASH_SOURCE[0]}"
capture 'Lock identity' sha256sum flake.lock
capture 'Pinned nixpkgs revision' python3 -c 'import json; print(json.load(open("flake.lock"))["nodes"]["nixpkgs"]["locked"]["rev"])'
capture 'Nix version' nix --version
capture 'NixOS version' nixos-version
capture 'Running closure' readlink -f /run/current-system
capture 'Running derivation' nix-store --query --deriver /run/current-system
capture 'Running closure size' nix path-info -S /run/current-system
capture 'CPU topology' lscpu
capture 'Microcode' bash -c 'sed -n "/^microcode/{p;q;}" /proc/cpuinfo'
# Loop variables intentionally expand in the child shell.
# shellcheck disable=SC2016
capture 'CPU online and SMT' bash -c 'for f in /sys/devices/system/cpu/online /sys/devices/system/cpu/smt/active; do printf "%s: " "$f"; cat "$f"; done'
# shellcheck disable=SC2016
capture 'CPU policies' bash -c 'for p in /sys/devices/system/cpu/cpufreq/policy*; do for n in scaling_driver scaling_governor energy_performance_preference; do f="$p/$n"; if test -r "$f"; then printf "%s: " "$f"; cat "$f"; fi; done; done'
capture 'Kernel command line' cat /proc/cmdline
# shellcheck disable=SC2016
capture 'BIOS' bash -c 'for n in bios_version bios_date; do printf "%s: " "$n"; cat "/sys/class/dmi/id/$n"; done'
# The ABI can expose several component versions; retain all blocks verbatim.
# shellcheck disable=SC2016
capture 'Intel ME firmware components' bash -c 'found=0; for f in /sys/class/mei/mei*/fw_ver; do test -r "$f" || continue; found=1; printf "%s:\n" "$f"; cat "$f"; done; if test "$found" = 0; then printf "ME firmware interface unavailable\n"; exit 1; fi'
capture 'Memory' free -h
capture 'Memory pressure' cat /proc/pressure/memory
capture 'CPU pressure' cat /proc/pressure/cpu
capture 'I/O pressure' cat /proc/pressure/io
capture 'VM counters' cat /proc/vmstat
capture 'Interrupt distribution' cat /proc/interrupts
capture 'IRQ balancing service' systemctl show irqbalance.service -p LoadState -p ActiveState
# shellcheck disable=SC2016
capture 'IRQ effective affinity' bash -c 'for f in /proc/irq/*/effective_affinity_list; do test -r "$f" || continue; printf "%s: " "$f"; cat "$f"; done'
# shellcheck disable=SC2016
capture 'NVMe schedulers' bash -c 'for f in /sys/block/nvme*n*/queue/scheduler; do test -r "$f" || continue; printf "%s: " "$f"; cat "$f"; done'
# shellcheck disable=SC2016
capture 'Zswap and THP defrag' bash -c 'for f in /sys/module/zswap/parameters/enabled /sys/kernel/mm/transparent_hugepage/defrag; do test -r "$f" || continue; printf "%s: " "$f"; cat "$f"; done'
capture 'Swap' swapon --show
capture 'ZRAM' zramctl
capture 'Transparent huge pages' cat /sys/kernel/mm/transparent_hugepage/enabled
capture 'PCI devices and drivers' lspci -nnk
capture 'Vulkan summary' vulkaninfo --summary
capture 'OpenGL version (current display)' glxinfo -B
printf '\nThe summary above does not itself prove 32-bit Vulkan rendering.\nAccepted practical ELF32 rendering evidence is retained separately in\ndocs/baselines/pre-optimization/vulkan32-render-20261005.txt.\n'
capture 'Block devices' lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL,REV
# shellcheck disable=SC2016
capture 'Filesystem topology by containing path' bash -c 'for m in / /home /var /nix /persist /.snapshots /boot /var/lib/nixos-optimization; do printf "\n%s\n" "$m"; findmnt -rn -o TARGET,SOURCE,FSROOT,FSTYPE,OPTIONS --target "$m" || exit; done'
capture_privileged 'Btrfs usage' btrfs filesystem usage /
capture_privileged 'Btrfs devices' btrfs device usage /
capture_privileged 'Btrfs scrub status' btrfs scrub status /
capture_privileged 'Btrfs device error counters' btrfs device stats /
for controller in /sys/class/nvme/nvme*; do
  test -e "$controller" || continue
  capture_privileged "NVMe SMART: ${controller##*/}" nvme smart-log "/dev/${controller##*/}"
  capture_privileged "NVMe latest error: ${controller##*/}" nvme error-log "/dev/${controller##*/}" --log-entries=1
done
capture 'Kernel' uname -a
capture 'Boot ID' cat /proc/sys/kernel/random/boot_id
capture 'systemd version' systemctl --version
capture 'Failed units' systemctl --failed --no-pager
capture 'Running services' systemctl list-units --type=service --state=running --no-pager
capture 'Maintenance timers' systemctl list-timers --all --no-pager
capture 'Loaded modules' lsmod
capture 'Observed temperatures' sensors
capture 'Commander Core service' systemctl show commander-core.service -p ActiveState -p SubState -p MainPID -p WatchdogUSec -p FragmentPath
capture 'Declared cooling policy source' sha256sum modules/hardware/commander-core/default.nix modules/hardware/commander-core/keeper.py hosts/desktop/default.nix
capture 'Cooling runtime state' cat /run/commander-core.state
capture_privileged 'Root subvolume' btrfs subvolume show /
capture 'Machine ID' cat /etc/machine-id
capture 'Reset diagnostic metadata' stat -c '%a %U:%G %s bytes %y' /persist/ephemeral-root-reset.log
capture_privileged 'Reset diagnostic counts' awk '/BEGIN boot_id=/{boots++} /RESET complete/{resets++} /RECOVERY complete/{recoveries++} END {printf "boot records=%d reset completions=%d recovery completions=%d\n", boots, resets, recoveries}' /persist/ephemeral-root-reset.log
printf '\nPrivileged reset log and secret files are deliberately not copied into this report.\n'
printf 'Failed commands above are missing evidence and must be resolved before final acceptance.\n'
