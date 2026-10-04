{
  config,
  inputs,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.hardware.commanderCore;

  liquidctlPr886 = import ../../../packages/liquidctl-pr886.nix {
    inherit inputs pkgs;
  };

  pythonEnv = pkgs.python3.withPackages (_pythonPackages: [
    liquidctlPr886.pythonPackage
  ]);

  commanderCoreKeeper = pkgs.writeShellScriptBin "commander-core-keeper" ''
    exec ${pythonEnv}/bin/python \
      ${./keeper.py} \
      "$@"
  '';
in
{
  options.hardware.commanderCore = {
    enable = lib.mkEnableOption "Corsair Commander Core cooling controller";

    usbId = lib.mkOption {
      type = lib.types.str;
      description = "Commander Core USB vendor:product identifier.";
    };

    serial = lib.mkOption {
      type = lib.types.str;
      description = "Serial number of the physical Commander Core.";
    };

    cooling = {
      baseFanDuty = lib.mkOption {
        type = lib.types.ints.between 0 100;
        default = 60;
      };

      highFanDuty = lib.mkOption {
        type = lib.types.ints.between 0 100;
        default = 100;
      };

      pumpDuty = lib.mkOption {
        type = lib.types.ints.between 0 100;
        default = 100;
      };

      highTemp = lib.mkOption {
        type = lib.types.number;
        default = 65;
      };

      highDelay = lib.mkOption {
        type = lib.types.number;
        default = 1;
      };

      lowTemp = lib.mkOption {
        type = lib.types.number;
        default = 60;
      };

      lowDelay = lib.mkOption {
        type = lib.types.number;
        default = 10;
      };

      tempInterval = lib.mkOption {
        type = lib.types.number;
        default = 1;
      };

      wakeInterval = lib.mkOption {
        type = lib.types.number;
        default = 10;
      };

      resetDelay = lib.mkOption {
        type = lib.types.number;
        default = 3;
      };
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.cooling.lowTemp <= cfg.cooling.highTemp;
        message = "hardware.commanderCore.cooling.lowTemp must be <= highTemp";
      }
    ];

    boot.kernelModules = [
      "coretemp"
    ];

    environment.systemPackages = [
      liquidctlPr886.application
    ];

    systemd.services.commander-core = {
      description = "Corsair Commander Core cooling controller";

      wantedBy = [
        "multi-user.target"
      ];

      after = [
        "systemd-udevd.service"
      ];

      serviceConfig = {
        Type = "notify";
        NotifyAccess = "main";

        ExecStart = ''
          ${commanderCoreKeeper}/bin/commander-core-keeper \
            --usbreset ${pkgs.usbutils}/bin/usbreset \
            --usb-id ${lib.escapeShellArg cfg.usbId} \
            --usb-serial ${lib.escapeShellArg cfg.serial} \
            --base-fan-duty ${toString cfg.cooling.baseFanDuty} \
            --high-fan-duty ${toString cfg.cooling.highFanDuty} \
            --pump-duty ${toString cfg.cooling.pumpDuty} \
            --high-temp ${toString cfg.cooling.highTemp} \
            --high-delay ${toString cfg.cooling.highDelay} \
            --low-temp ${toString cfg.cooling.lowTemp} \
            --low-delay ${toString cfg.cooling.lowDelay} \
            --temp-interval ${toString cfg.cooling.tempInterval} \
            --wake-interval ${toString cfg.cooling.wakeInterval} \
            --reset-delay ${toString cfg.cooling.resetDelay}
        '';

        Restart = "on-failure";
        RestartSec = "5s";

        WatchdogSec = "35s";
        TimeoutStopSec = "10s";
      };
    };
  };
}
