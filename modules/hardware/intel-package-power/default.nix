{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.hardware.intelPackagePower;
in
{
  options.hardware.intelPackagePower = {
    enable = lib.mkEnableOption "Intel package-0 RAPL power limits at boot and resume";
    pl1Watts = lib.mkOption {
      type = lib.types.ints.positive;
      description = "Long-term package power limit in watts.";
    };
    pl2Watts = lib.mkOption {
      type = lib.types.ints.positive;
      description = "Short-term package power limit in watts.";
    };
  };
  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.pl2Watts >= cfg.pl1Watts;
        message = "Intel package PL2 must be at least PL1.";
      }
    ];
    systemd.services.cpu-package-power-limit = {
      description = "Apply the desktop ${toString cfg.pl1Watts}W CPU package power baseline";
      wantedBy = [ "multi-user.target" ];
      after = [ "systemd-modules-load.service" ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
      };
      script = ''
        set -eu
        zone=/sys/class/powercap/intel-rapl:0
        test "$(cat "$zone/name")" = package-0
        test "$(cat "$zone/enabled")" = 1
        test "$(cat "$zone/constraint_0_name")" = long_term
        test "$(cat "$zone/constraint_1_name")" = short_term
        printf '%s\n' ${toString (cfg.pl1Watts * 1000000)} > "$zone/constraint_0_power_limit_uw"
        printf '%s\n' ${toString (cfg.pl2Watts * 1000000)} > "$zone/constraint_1_power_limit_uw"
        test "$(cat "$zone/constraint_0_power_limit_uw")" = ${toString (cfg.pl1Watts * 1000000)}
        test "$(cat "$zone/constraint_1_power_limit_uw")" = ${toString (cfg.pl2Watts * 1000000)}
      '';
      path = [ pkgs.coreutils ];
    };

    powerManagement.resumeCommands = ''
      ${pkgs.systemd}/bin/systemctl restart cpu-package-power-limit.service
    '';

  };
}
