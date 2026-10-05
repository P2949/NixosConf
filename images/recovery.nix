{ pkgs, modulesPath, ... }:

{
  imports = [ (modulesPath + "/installer/cd-dvd/installation-cd-minimal.nix") ];

  networking.hostName = "nixos-recovery";

  # Independent pinned rescue environment; never import workstation disks,
  # persistence, passwords, cooling control or destructive reset behavior.
  environment.systemPackages = with pkgs; [
    btrfs-progs
    nvme-cli
    util-linux
    git
    curl
    vim
    pciutils
    usbutils
    lm_sensors
    efibootmgr
  ];

  system.stateVersion = "26.05";
}
