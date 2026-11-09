{ ... }:

{
  imports = [
    ./vm.nix
    ./hardware-configuration.nix
    ./disko.nix
    ./persistence.nix
    ./ephemeral-root.nix
    ./stutter-validation-kernels.nix
    ./stutter-validation.nix
    ./stutter-service.nix
    ./minecraft
    ./gpu-policy.nix

    ../../profiles/workstation.nix
    ../../modules/workstation/optimization-boundary.nix

    ../../modules/storage/btrfs-maintenance
    ../../modules/workstation/activation-safety
    ../../modules/hardware/intel-package-power
    ../../modules/hardware/commander-core
  ];

  networking.hostName = "desktop";

  # Stutter's bounded always-on service (controller as the desktop account plus a root worker).
  # The binary is the release build of the Stutter commit pinned in flake.nix, added to the store
  # with `nix-store --add-fixed sha256` and pinned here by the hash of the file.
  services.stutterBounded = {
    enable = true;
    binarySha256 = "459a3a3f717571f782f0a28655bacd2e59f9af3048cc058bd9e63f68c2436f63";
  };

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

  hardware.bluetooth = {
    enable = false;
    powerOnBoot = false;
  };

  hardware.intelPackagePower = {
    enable = true;
    pl1Watts = 125;
    pl2Watts = 125;
  };

  hardware.commanderCore = {
    enable = true;

    usbId = "1b1c:0c1c";
    serial = "e3072091824547ba7680aee53091005f";

    cooling = {
      baseFanDuty = 60;
      highFanDuty = 100;
      pumpDuty = 100;

      # Start the mechanical fan ramp before short CPU load spikes peak.
      # Keep idle duty and firmware policy unchanged; retain hysteresis.
      highTemp = 50;
      highDelay = 0;

      lowTemp = 45;
      lowDelay = 30;

      tempInterval = 0.5;
      wakeInterval = 10;
      resetDelay = 3;
    };
  };

  system.stateVersion = "26.05";
}
