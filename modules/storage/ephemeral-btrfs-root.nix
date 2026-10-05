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
  resetScript =
    builtins.replaceStrings
      [
        "@NIX_TOP@"
        "@NIX_ROOT_DEVICE@"
        "@NIX_ROOT_NAME@"
        "@NIX_NEXT_NAME@"
        "@NIX_PERSIST_NAME@"
        "@NIX_LOG_RELATIVE@"
        "@NIX_ALLOWED_DESCENDANT_CHECK@"
      ]
      [
        (lib.escapeShellArg topLevelMount)
        (lib.escapeShellArg rootDevice)
        (lib.escapeShellArg cfg.rootSubvolume)
        (lib.escapeShellArg cfg.stagingSubvolume)
        (lib.escapeShellArg cfg.persistenceSubvolume)
        (lib.escapeShellArg cfg.logFile)
        allowedDescendantCheck
      ]
      (builtins.readFile ./ephemeral-root-reset.sh);

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
          builtins.match "([A-Za-z0-9_@][A-Za-z0-9_.@-]*/)*[A-Za-z0-9_@][A-Za-z0-9_.@-]*" cfg.logFile != null
          && !(lib.hasInfix ".." cfg.logFile);
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

      script = resetScript;
    };
  };
}
