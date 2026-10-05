{ pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    git
    git-lfs

    curl

    vim

    pciutils
    efibootmgr
    usbutils
    lm_sensors
    alsa-utils
    btrfs-progs
    nvme-cli
    unzip

    file
    which
  ];
}
