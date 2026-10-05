{ ... }:

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

  hardware.commanderCore = {
    enable = true;

    usbId = "1b1c:0c1c";
    serial = "e3072091824547ba7680aee53091005f";

    cooling = {
      baseFanDuty = 60;
      highFanDuty = 100;
      pumpDuty = 100;

      highTemp = 65;
      highDelay = 1;

      lowTemp = 60;
      lowDelay = 10;

      tempInterval = 1;
      wakeInterval = 10;
      resetDelay = 3;
    };
  };

  system.stateVersion = "26.05";
}
