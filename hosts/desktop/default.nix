{ ... }:

{
  imports = [
    ./hardware-configuration.nix
    ./disko.nix
    ./persistence.nix

    ../../profiles/workstation.nix

    ../../modules/hardware/commander-core
  ];

  networking.hostName = "desktop";

  boot.loader.systemd-boot = {
    enable = true;
    configurationLimit = 20;
  };

  boot.loader.efi.canTouchEfiVariables = true;

  hardware.enableRedistributableFirmware = true;
  hardware.cpu.intel.updateMicrocode = true;

  services.btrfs.autoScrub = {
    enable = true;
    interval = "monthly";
    fileSystems = [ "/" ];
  };

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
