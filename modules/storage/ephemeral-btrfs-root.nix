{
  config,
  lib,
  pkgs,
  utils,
  ...
}:

let
  cfg = config.boot.ephemeralBtrfsRoot;

  rootFs = config.fileSystems."/";
  rootDevice = if rootFs.device == null then "" else rootFs.device;
  rootDeviceUnit = "${utils.escapeSystemdPath rootDevice}.device";

  topLevelMount = "/run/ephemeral-root-btrfs";

  safeSubvolumeName = name: builtins.match "[A-Za-z0-9_@][A-Za-z0-9_.@-]*" name != null;
  subvolumeNames = [
    cfg.rootSubvolume
    cfg.stagingSubvolume
    cfg.persistenceSubvolume
  ];
  rootSubvolumeOptions = lib.filter (lib.hasPrefix "subvol=") rootFs.options;

  allowedSubvolumePaths = map (
    descendant: "${cfg.rootSubvolume}/${descendant}"
  ) cfg.allowedDescendants;

  allowedDescendantCheck =
    if allowedSubvolumePaths == [ ] then
      "false"
    else
      lib.concatMapStringsSep " || " (
        path: ''[[ "$candidate" == ${lib.escapeShellArg path} ]]''
      ) allowedSubvolumePaths;
in
{
  options.boot.ephemeralBtrfsRoot = {
    enable = lib.mkEnableOption "Btrfs ephemeral root reset in the systemd initrd";

    rootSubvolume = lib.mkOption {
      type = lib.types.str;
      default = "@root";
      description = "Direct top-level Btrfs subvolume reset at boot; must match the / subvol= mount option.";
    };

    stagingSubvolume = lib.mkOption {
      type = lib.types.str;
      default = "@root-next";
      description = "Direct top-level staging subvolume; recovery and cleanup require it to be completely empty.";
    };

    persistenceSubvolume = lib.mkOption {
      type = lib.types.str;
      default = "@persist";
      description = "Distinct direct top-level persistence subvolume holding the reset log.";
    };

    allowedDescendants = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [
        "tmp"
        "srv"
      ];
      description = "Direct disposable child subvolumes permitted under root. All other descendants stop reset.";
    };

    logFile = lib.mkOption {
      type = lib.types.str;
      default = "ephemeral-root-reset.log";
      description = "Log path relative to the persistence subvolume; written with mode 0600 before deletion.";
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = config.boot.initrd.systemd.enable;
        message = "boot.ephemeralBtrfsRoot requires a systemd initrd.";
      }
      {
        assertion = rootFs.fsType == "btrfs";
        message = "boot.ephemeralBtrfsRoot requires / to use Btrfs.";
      }
      {
        assertion = rootDevice != "";
        message = "boot.ephemeralBtrfsRoot requires a concrete root device.";
      }
      {
        assertion = lib.all safeSubvolumeName subvolumeNames;
        message = "Root, staging and persistence must be safe direct Btrfs subvolume names.";
      }
      {
        assertion = builtins.length (lib.unique subvolumeNames) == 3;
        message = "The root, staging and persistence Btrfs subvolumes must all differ.";
      }
      {
        assertion =
          builtins.length rootSubvolumeOptions == 1
          && lib.elem (builtins.head rootSubvolumeOptions) [
            "subvol=${cfg.rootSubvolume}"
            "subvol=/${cfg.rootSubvolume}"
          ]
          && !(lib.any (lib.hasPrefix "subvolid=") rootFs.options);
        message = "The / mount must select boot.ephemeralBtrfsRoot.rootSubvolume with one matching subvol= option and no subvolid= override.";
      }
      {
        assertion = lib.all safeSubvolumeName cfg.allowedDescendants;
        message = "allowedDescendants must contain direct relative subvolume names only.";
      }
      {
        assertion =
          cfg.logFile != "" && !(lib.hasPrefix "/" cfg.logFile) && !(lib.hasInfix ".." cfg.logFile);
        message = "logFile must be a safe path relative to the persistence subvolume.";
      }
    ];

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

      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
      };

      script = ''
        set -euo pipefail

        top=${lib.escapeShellArg topLevelMount}
        root_device=${lib.escapeShellArg rootDevice}
        root_name=${lib.escapeShellArg cfg.rootSubvolume}
        next_name=${lib.escapeShellArg cfg.stagingSubvolume}
        persist_name=${lib.escapeShellArg cfg.persistenceSubvolume}
        log_relative=${lib.escapeShellArg cfg.logFile}

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

        mkdir -p "$(dirname "$log_file")"
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

          if (( ''${#entries[@]} != 0 )); then
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

        root_descendants=()
        descendant_output="$(btrfs subvolume list -o "$root")"

        if [[ -n "$descendant_output" ]]; then
          while IFS= read -r line; do
            if [[ "$line" != *" path "* ]]; then
              log "FAIL: could not parse descendant line: $line"
              exit 1
            fi

            candidate="''${line#* path }"

            if ! ( ${allowedDescendantCheck} ); then
              log "FAIL: refusing to delete unknown root descendant: $candidate"
              exit 1
            fi

            # The root-level list may only expose direct children. Every
            # allowed child must itself have no nested subvolumes.
            require_no_descendants "$top/$candidate" "$candidate"

            root_descendants+=("$candidate")
          done <<< "$descendant_output"
        fi

        if (( ''${#root_descendants[@]} == 0 )); then
          log "root descendant audit passed: none present"
        else
          for candidate in "''${root_descendants[@]}"; do
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

        for candidate in "''${root_descendants[@]}"; do
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
      '';
    };
  };
}
