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

  # Give large development workloads (Unreal, clangd, IDEs, etc.)
  # a practical open-file limit while retaining a finite hard ceiling.
  security.pam.loginLimits = [
    {
      domain = "p2949";
      type = "soft";
      item = "nofile";
      value = 65536;
    }
  ];

  # User systemd services do not inherit PAM limits, so configure
  # the user manager independently.
  systemd.user.extraConfig = ''
    DefaultLimitNOFILE=65536:524288
  '';

  services.btrfs.autoScrub = {
    enable = true;
    interval = "monthly";
    fileSystems = [ "/" ];
  };

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

  system.stateVersion = "26.05";
}
