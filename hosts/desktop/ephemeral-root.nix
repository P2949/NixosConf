{
  config,
  lib,
  pkgs,
  utils,
  ...
}:

let
  rootDevice = config.fileSystems."/".device;
  rootDeviceUnit = "${utils.escapeSystemdPath rootDevice}.device";

  topLevelMount = "/run/ephemeral-root-btrfs";
in
{
  boot.initrd.systemd.initrdBin = [
    pkgs.btrfs-progs
    pkgs.coreutils
    pkgs.util-linux
  ];

  boot.initrd.systemd.services.ephemeral-root-reset = {
    description = "Reset Btrfs root subvolume";

    requiredBy = [
      "sysroot.mount"
    ];

    requires = [
      rootDeviceUnit
    ];

    bindsTo = [
      rootDeviceUnit
    ];

    after = [
      rootDeviceUnit
      "systemd-hibernate-resume.service"
    ];

    before = [
      "sysroot.mount"
      "shutdown.target"
    ];

    conflicts = [
      "shutdown.target"
    ];

    unitConfig.DefaultDependencies = false;

    serviceConfig.Type = "oneshot";

    script = ''
      set -euo pipefail

      top=${lib.escapeShellArg topLevelMount}
      root="$top/@root"
      next="$top/@root-next"

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
        ${lib.escapeShellArg rootDevice} \
        "$top"

      if [[ ! -e "$root" ]]; then
        if [[ -e "$next" ]]; then
          if ! btrfs subvolume show "$next" >/dev/null 2>&1; then
            echo "FAIL: @root-next exists but is not a Btrfs subvolume" >&2
            exit 1
          fi

          echo "Recovering interrupted root reset from @root-next"
          mv "$next" "$root"
          sync
          exit 0
        fi

        echo "FAIL: neither @root nor recoverable @root-next exists" >&2
        exit 1
      fi

      if ! btrfs subvolume show "$root" >/dev/null 2>&1; then
        echo "FAIL: @root exists but is not a Btrfs subvolume" >&2
        exit 1
      fi

      if [[ -e "$next" ]]; then
        if ! btrfs subvolume show "$next" >/dev/null 2>&1; then
          echo "FAIL: @root-next exists but is not a Btrfs subvolume" >&2
          exit 1
        fi

        btrfs subvolume delete \
          -R \
          -c \
          "$next"
      fi

      btrfs subvolume create "$next"

      btrfs subvolume delete \
        -R \
        -c \
        "$root"

      mv "$next" "$root"

      sync
    '';
  };
}
