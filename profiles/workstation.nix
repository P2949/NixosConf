{ ... }:

{
  imports = [
    ../modules/core
    ../modules/desktop
    ../modules/gaming
    ../modules/compatibility/nix-ld.nix
  ];

  networking.networkmanager.enable = true;

  hardware.bluetooth = {
    enable = false;
    powerOnBoot = false;
  };

  security.polkit.enable = true;

  services.udisks2.enable = true;
  services.gvfs.enable = true;

  programs.firefox.enable = true;
}
