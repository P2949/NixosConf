{
  inputs,
  pkgs,
  ...
}:

let
  liquidctlPr886Python =
    pkgs.python3Packages.liquidctl.overrideAttrs (_old: {
      version = "1.17.0.dev22+g48e8dd07b";

      src = inputs.liquidctl-pr886;
    });

  liquidctlPr886 =
    pkgs.python3Packages.toPythonApplication liquidctlPr886Python;

  pythonEnv =
    pkgs.python3.withPackages (_pythonPackages: [
      liquidctlPr886Python
    ]);

  commanderCoreKeeper =
    pkgs.writeShellScriptBin "commander-core-keeper" ''
      exec ${pythonEnv}/bin/python \
        ${./commander-core-keeper.py} \
        "$@"
    '';
in
{
  # Ensure the CPU package temperature interface exists.
  boot.kernelModules = [
    "coretemp"
  ];

  # Expose the exact liquidctl build for diagnostics too.
  environment.systemPackages = [
    liquidctlPr886
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
          --usb-id 1b1c:0c1c \
          --usb-serial e3072091824547ba7680aee53091005f \
          --base-fan-duty 60 \
          --high-fan-duty 100 \
          --pump-duty 100 \
          --high-temp 65 \
          --high-delay 1 \
          --low-temp 60 \
          --low-delay 10 \
          --temp-interval 1 \
          --wake-interval 10 \
          --reset-delay 3
      '';

      Restart = "on-failure";
      RestartSec = "5s";

      # Old OpenRC health policy allowed roughly 35 seconds without
      # a successful WAKE.  systemd now provides the supervision.
      WatchdogSec = "35s";

      TimeoutStopSec = "10s";
    };
  };
}
