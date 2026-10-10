{ ... }:

{
  imports = [
    ../modules/core
    ../modules/desktop
    ../modules/gaming
    ../modules/compatibility/nix-ld.nix
  ];

  networking.networkmanager.enable = true;

  security.polkit.enable = true;

  services.udisks2.enable = true;
  services.gvfs.enable = true;

  programs.firefox.enable = true;
}
