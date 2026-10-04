{ pkgs, ... }:

{
  networking.hostName = "desktop";

  time.timeZone = "Europe/Dublin";

  i18n.defaultLocale = "en_IE.UTF-8";

  nixpkgs.config.allowUnfree = true;

  nix.settings = {
    experimental-features = [
      "nix-command"
      "flakes"
    ];

    trusted-users = [
      "root"
      "p2949"
    ];

    auto-optimise-store = true;
  };

  boot.loader.systemd-boot = {
    enable = true;
    configurationLimit = 20;
  };

  boot.loader.efi.canTouchEfiVariables = true;

  hardware.enableRedistributableFirmware = true;
  hardware.cpu.intel.updateMicrocode = true;

  networking.networkmanager.enable = true;

  hardware.bluetooth = {
    enable = true;
    powerOnBoot = true;
  };

  users.users.p2949 = {
    isNormalUser = true;

    extraGroups = [
      "wheel"
      "networkmanager"
      "video"
      "render"
      "audio"
      "input"
      "kvm"
    ];

    shell = pkgs.zsh;
  };

  programs.zsh.enable = true;

  security.polkit.enable = true;
  security.sudo.enable = true;

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

  system.stateVersion = "26.05";
}
