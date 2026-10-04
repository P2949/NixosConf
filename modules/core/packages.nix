{ pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    git
    git-lfs
    gh

    curl
    wget

    vim
    nano

    ripgrep
    fd
    jq

    btop
    htop

    pciutils
    efibootmgr
    usbutils
    lm_sensors
    alsa-utils
    btrfs-progs
    nvme-cli
    unzip

    tree
    file
    which

    gcc
    clang
    lld
    gdb

    cmake
    ninja
    gnumake
    pkg-config

    python3
  ];
}
