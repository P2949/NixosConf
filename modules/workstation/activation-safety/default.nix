{
  config,
  lib,
  pkgs,
  username,
  ...
}:
let
  cfg = config.workstation.activationSafety;
  root = lib.attrByPath [ "boot" "ephemeralBtrfsRoot" ] {
    rootSubvolume = "@root";
    stagingSubvolume = "@root-next";
    persistenceSubvolume = "@persist";
    allowedDescendants = [ ];
  } config;
  rootDevice = lib.attrByPath [ "fileSystems" "/" "device" ] "" config;
  bootDevice = lib.attrByPath [ "fileSystems" "/boot" "device" ] "" config;
  secret = lib.attrByPath [ "users" "users" username "hashedPasswordFile" ] null config;
  concrete = value: builtins.isString value && value != "";
  checker = pkgs.writeShellApplication {
    name = "workstation-activation-check";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.util-linux
      pkgs.btrfs-progs
    ];
    text = ''
      expected_device=${lib.escapeShellArg rootDevice}
      expected_boot_device=${lib.escapeShellArg bootDevice}
      secret_file=${lib.escapeShellArg (if concrete secret then secret else "")}
      root_name=${lib.escapeShellArg root.rootSubvolume}
      next_name=${lib.escapeShellArg root.stagingSubvolume}
      persist_name=${lib.escapeShellArg root.persistenceSubvolume}
      allowed_descendants=( ${lib.escapeShellArgs root.allowedDescendants} )
      esp_reserve=${toString cfg.espReserveBytes}
      ${builtins.readFile ./check.sh}
    '';
  };
in
{
  options.workstation.activationSafety = {
    enable = lib.mkEnableOption "physical workstation activation prerequisites";
    espReserveBytes = lib.mkOption {
      type = lib.types.ints.positive;
      description = "Measured free-space reserve required on the ESP before activation.";
    };
  };
  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion =
          lib.hasAttrByPath [ "boot" "ephemeralBtrfsRoot" ] config
          && concrete rootDevice
          && lib.attrByPath [ "fileSystems" "/" "fsType" ] "" config == "btrfs";
        message = "workstation.activationSafety requires the ephemeral Btrfs root contract and a concrete Btrfs / filesystem (reset may be disabled for recovery).";
      }
      {
        assertion =
          concrete bootDevice && lib.attrByPath [ "fileSystems" "/boot" "fsType" ] "" config == "vfat";
        message = "workstation.activationSafety requires a concrete vfat /boot filesystem.";
      }
      {
        assertion = concrete secret;
        message = "workstation.activationSafety requires a configured hashedPasswordFile for the selected user.";
      }
    ];
    system.preSwitchChecks = lib.genAttrs [ "persistence" "credentials" "esp" "topology" ] (
      role: ''${lib.getExe checker} ${lib.escapeShellArg role} "$@"''
    );
  };
}
