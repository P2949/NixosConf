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
    inherit pkgs;
    src = inputs.liquidctl-pr886;
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
        assertion = builtins.match "[0-9a-fA-F]{4}:[0-9a-fA-F]{4}" cfg.usbId != null;
        message = "hardware.commanderCore.usbId must be four hex digits, a colon, and four hex digits (for example 1b1c:0c1c).";
      }
      {
        assertion = builtins.match "[[:space:]]*" cfg.serial == null;
        message = "hardware.commanderCore.serial must contain a non-whitespace device serial.";
      }
      {
        assertion = cfg.cooling.baseFanDuty <= cfg.cooling.highFanDuty;
        message = "hardware.commanderCore.cooling.baseFanDuty must be <= highFanDuty.";
      }
      {
        assertion =
          cfg.cooling.lowTemp >= 0
          && cfg.cooling.highTemp <= 100
          && cfg.cooling.lowTemp < cfg.cooling.highTemp;
        message = "hardware.commanderCore.cooling requires 0 <= lowTemp < highTemp <= 100 Celsius for strict hysteresis.";
      }
      {
        assertion = lib.all (value: value > 0) [
          cfg.cooling.tempInterval
          cfg.cooling.wakeInterval
          cfg.cooling.resetDelay
        ];
        message = "hardware.commanderCore.cooling tempInterval, wakeInterval and resetDelay must be strictly positive seconds.";
      }
      {
        assertion = cfg.cooling.highDelay >= 0 && cfg.cooling.lowDelay >= 0;
        message = "hardware.commanderCore.cooling highDelay and lowDelay must be nonnegative seconds.";
      }
      {
        assertion = 2 * lib.max cfg.cooling.tempInterval cfg.cooling.wakeInterval < 35;
        message = "hardware.commanderCore.cooling tempInterval and wakeInterval must each be below 17.5 seconds to leave two intervals of margin within the 35-second watchdog.";
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
