{
  config,
  lib,
  pkgs,
  modulesPath,
  ...
}:
{
  imports = [
    "${modulesPath}/profiles/minimal.nix"
    "${modulesPath}/installer/netboot/netboot.nix"
  ];
  system.stateVersion = "26.05";
  networking.hostName = "diagnostic";
  networking.useNetworkd = true;
  networking.useDHCP = lib.mkDefault true;
  boot.initrd.systemd.enable = true;
  boot.kernelParams = [ "console=ttyS0,115200n8" ];
  # A temporary diagnostic session has no shipped login credential.
  users.allowNoPasswordLogin = true;
  users.users.root.hashedPassword = "!";
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
    pkgs.stress-ng
    pkgs.btrfs-progs
    pkgs.nvme-cli
    pkgs.smartmontools
    pkgs.pciutils
    pkgs.usbutils
    pkgs.kexec-tools
  ];
  systemd.services.diagnostic-ready = {
    wantedBy = [ "multi-user.target" ];
    requires = [ "sshd.service" ];
    after = [ "sshd.service" ];
    path = [
      pkgs.coreutils
      pkgs.util-linux
      pkgs.iproute2
      pkgs.gnugrep
    ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };
    script = ''
      exec >/dev/ttyS0 2>&1
      test "$(hostname)" = diagnostic
      test "$(findmnt --first-only --target / -n -o FSTYPE)" = tmpfs
      test "$(findmnt --first-only --target /nix/store -n -o FSTYPE)" = overlay
      test ! -e /run/before-kexec
      for attempt in $(seq 1 60); do
        if ip -4 route show default | grep -q default; then break; fi
        sleep 1
      done
      ip -4 route show default | grep -q default
      systemctl is-active --quiet sshd.service
      test -x ${pkgs.perf}/bin/perf
      test -x ${config.boot.kernelPackages.turbostat}/bin/turbostat
      test -x ${pkgs.stress-ng}/bin/stress-ng
      test -x ${pkgs.btrfs-progs}/bin/btrfs
      test -x ${pkgs.nvme-cli}/bin/nvme
      echo "DIAGNOSTIC_BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)"
      echo DIAGNOSTIC_READY
    '';
  };
}
