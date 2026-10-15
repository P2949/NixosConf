{
  config,
  lib,
  modulesPath,
  pkgs,
  benchmarkRunner,
  ...
}:
{
  imports = [
    "${modulesPath}/profiles/image-based-appliance.nix"
    "${modulesPath}/image/repart.nix"
  ];

  system.stateVersion = "26.05";
  # No credential is shipped. An operator can add SSH public keys declaratively.
  users.allowNoPasswordLogin = true;
  users.users.root.hashedPassword = "!";
  system.image = {
    id = "benchmark-appliance";
    version = "1";
  };
  image.repart = {
    compression.enable = false;
    verityStore = {
      enable = true;
      ukiPath = "/EFI/BOOT/BOOT${lib.toUpper pkgs.stdenv.hostPlatform.efiArch}.EFI";
    };
    partitions."00-esp".repartConfig = {
      Type = "esp";
      Format = "vfat";
      SizeMinBytes = "96M";
    };
  };

  fileSystems."/" = {
    fsType = "tmpfs";
    options = [ "mode=0755" ];
  };
  boot = {
    loader.grub.enable = false;
    initrd.systemd.enable = true;
    initrd.availableKernelModules = [
      "virtio_pci"
      "virtio_blk"
      "virtio_scsi"
    ];
    kernelParams = [
      "console=ttyS0,115200n8"
      "systemd.verity_usr_options=panic-on-corruption"
      "systemd.show_status=1"
    ];
  };
  # /usr is protected by dm-verity; activation must not create /usr/bin/env.
  system.activationScripts.usrbinenv = lib.mkForce "";

  networking = {
    hostName = "benchmark-appliance";
    useDHCP = lib.mkDefault true;
  };
  services.openssh = {
    enable = true;
    settings = {
      PasswordAuthentication = false;
      KbdInteractiveAuthentication = false;
      PermitRootLogin = "prohibit-password";
    };
  };
  environment.systemPackages = [
    pkgs.perf
    config.boot.kernelPackages.turbostat
    pkgs.hwloc
    pkgs.numactl
    pkgs.cryptsetup
    benchmarkRunner
  ];
  systemd.services.benchmark-appliance-health = {
    description = "Check the immutable benchmark appliance";
    wantedBy = [ "multi-user.target" ];
    requires = [ "sshd.service" ];
    after = [ "sshd.service" ];
    path = [
      pkgs.coreutils
      pkgs.util-linux
      pkgs.cryptsetup
      pkgs.iproute2
      pkgs.gnugrep
    ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      StandardOutput = "journal+console";
      StandardError = "journal+console";
    };
    script = ''
      exec >/dev/ttyS0 2>&1
      test "$(findmnt --first-only --target / -n -o FSTYPE)" = tmpfs
      test "$(findmnt --first-only --target /nix/store -n -o FSTYPE)" = erofs
      findmnt --first-only --target /nix/store -n -o OPTIONS | grep -Eq '(^|,)ro(,|$)'
      findmnt --first-only --target /nix/store -o TARGET,SOURCE,FSTYPE,OPTIONS
      veritysetup status usr
      for attempt in $(seq 1 60); do
        if ip -4 route show default | grep -q default; then break; fi
        sleep 1
      done
      ip -4 route show default | grep -q default
      systemctl is-active --quiet sshd.service
      test -x ${pkgs.perf}/bin/perf
      test -x ${config.boot.kernelPackages.turbostat}/bin/turbostat
      test -x ${pkgs.hwloc}/bin/lstopo-no-graphics
      test -x ${pkgs.numactl}/bin/numactl
      ${benchmarkRunner}/bin/nixos-optimization-nix-evaluation --help >/dev/null
      echo BENCHMARK_APPLIANCE_READY
    '';
  };
}
