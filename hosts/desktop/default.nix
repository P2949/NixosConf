{ pkgs, ... }:

{
  imports = [
    ./hardware-configuration.nix
    ./disko.nix
    ./persistence.nix
    ./ephemeral-root.nix

    ../../profiles/workstation.nix
    ../../modules/core/stock-control.nix

    ../../modules/storage/btrfs-maintenance
    ../../modules/workstation/activation-safety
    ../../modules/hardware/commander-core
  ];

  networking.hostName = "desktop";

  workstation.activationSafety = {
    enable = true;
    espReserveBytes = 256 * 1024 * 1024;
  };

  services.btrfs.autoScrub = {
    enable = true;
    interval = "*-*-01 02:00:00";
    fileSystems = [ "/" ];
  };

  boot.loader.systemd-boot = {
    enable = true;
    configurationLimit = 20;
  };

  boot.loader.efi.canTouchEfiVariables = true;

  hardware.enableRedistributableFirmware = true;
  hardware.cpu.intel.updateMicrocode = true;

  # The retained firmware leaves package power unconstrained. Apply the
  # selected workstation baseline at boot and again after suspend/resume.
  systemd.services.cpu-package-power-limit = {
    description = "Apply the desktop 125W CPU package power baseline";
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
      for constraint in 0 1; do
        printf '%s\n' 125000000 > "$zone/constraint_''${constraint}_power_limit_uw"
      done
      for constraint in 0 1; do
        test "$(cat "$zone/constraint_''${constraint}_power_limit_uw")" = 125000000
      done
    '';
    path = [ pkgs.coreutils ];
  };

  powerManagement.resumeCommands = ''
    ${pkgs.systemd}/bin/systemctl restart cpu-package-power-limit.service
  '';

  hardware.commanderCore = {
    enable = true;

    usbId = "1b1c:0c1c";
    serial = "e3072091824547ba7680aee53091005f";

    cooling = {
      baseFanDuty = 60;
      highFanDuty = 100;
      pumpDuty = 100;

      # Start the mechanical fan ramp before short CPU load spikes peak.
      # Keep idle duty and firmware policy unchanged; retain hysteresis.
      highTemp = 50;
      highDelay = 0;

      lowTemp = 45;
      lowDelay = 30;

      tempInterval = 0.5;
      wakeInterval = 10;
      resetDelay = 3;
    };
  };

  system.stateVersion = "26.05";
}
