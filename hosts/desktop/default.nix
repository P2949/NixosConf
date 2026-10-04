{ ... }:

{
  imports = [
    ./hardware-configuration.nix
    ./disko.nix

    ../../profiles/workstation.nix

    ../../modules/hardware/commander-core.nix
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

  system.stateVersion = "26.05";
}
