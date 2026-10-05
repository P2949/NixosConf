{
  config,
  lib,
  pkgs,
  username,
  ...
}:
let
  cfg = config.boot.workstationActivationSafety;
  root = config.boot.ephemeralBtrfsRoot;
  checker = pkgs.writeShellApplication {
    name = "workstation-activation-check";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.util-linux
      pkgs.btrfs-progs
    ];
    text = ''
      expected_device=${lib.escapeShellArg config.fileSystems."/".device}
      expected_boot_device=${lib.escapeShellArg config.fileSystems."/boot".device}
      secret_file=${lib.escapeShellArg config.users.users.${username}.hashedPasswordFile}
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
  options.boot.workstationActivationSafety = {
    enable = lib.mkEnableOption "physical workstation activation prerequisites";
    espReserveBytes = lib.mkOption {
      type = lib.types.ints.positive;
      description = "Measured free-space reserve required on the ESP before activation.";
    };
  };
  config = lib.mkIf cfg.enable {
    system.preSwitchChecks = lib.genAttrs [ "persistence" "credentials" "esp" "topology" ] (
      role: ''${lib.getExe checker} ${lib.escapeShellArg role} "$@"''
    );
  };
}
