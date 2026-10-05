{
  desktopSystem,
  inputs,
  pkgs,
  username,
}:
let
  inherit (pkgs) lib;
  diskDevice = "/dev/disk/by-id/virtio-reconstruction";
  installed = desktopSystem.extendModules {
    modules = [
      ({ modulesPath, ... }: {
        imports = [
          (modulesPath + "/testing/test-instrumentation.nix")
          (modulesPath + "/profiles/qemu-guest.nix")
        ];
        disko.devices.disk.main.device = lib.mkForce diskDevice;
        networking.hostName = lib.mkForce "reconstructed";
        hardware.commanderCore.enable = lib.mkForce false;
        boot.loader.efi.canTouchEfiVariables = lib.mkForce false;
        boot.loader.timeout = lib.mkForce 1;
        boot.kernelParams = [ "console=ttyS0" ];
        # Retain declared GC policy but never run maintenance in this fixture.
        systemd.timers.nix-gc.wantedBy = lib.mkForce [ ];
        systemd.timers."btrfs-scrub--".wantedBy = lib.mkForce [ ];
        systemd.timers.fstrim.wantedBy = lib.mkForce [ ];
      })
    ];
  };
  qemuCommon = import "${pkgs.path}/nixos/lib/qemu-common.nix" { inherit (pkgs) lib stdenv; };
in
pkgs.testers.runNixOSTest {
  name = "blank-disk-reconstruction";
  meta.timeout = 7200;
  nodes.installer = { lib, ... }: {
    imports = [
      inputs.disko.nixosModules.disko
      { disko.devices = desktopSystem.config.disko.devices; }
    ];
    disko.enableConfig = false;
    disko.devices.disk.main.device = lib.mkForce diskDevice;
    environment.systemPackages = [
      pkgs.nixos-install-tools
      pkgs.openssl
      pkgs.btrfs-progs
    ];
    virtualisation = {
      memorySize = 4096;
      cores = 2;
      # Avoid a label collision after target Btrfs is also labelled nixos.
      rootDevice = "/dev/disk/by-id/virtio-root";
      additionalPaths = [ installed.config.system.build.toplevel ];
      emptyDiskImages = [
        {
          size = 98304;
          driveConfig.deviceExtraOpts.serial = "reconstruction";
        }
      ];
    };
    system.stateVersion = "26.05";
  };
  testScript = { nodes, ... }: ''
    import json
    import shlex
    import shutil
    import tempfile
    from pathlib import Path

    installer.start()
    installer.wait_for_unit("multi-user.target")
    installer.succeed("test -b ${diskDevice}")
    # Prove no filesystem/signature exists before invoking the actual Disko layout.
    installer.succeed("test -z \"$(wipefs -n --noheadings -o TYPE ${diskDevice})\"")
    installer.succeed("${nodes.installer.system.build.diskoScript}")
    installer.succeed("install -d -m 0700 /mnt/persist/secrets")
    installer.succeed("openssl passwd -6 -salt reconstruction vm-test-only > /mnt/persist/secrets/${username}-password-hash")
    installer.succeed("chmod 0600 /mnt/persist/secrets/${username}-password-hash")
    installer.succeed("install -d /mnt/persist/etc")
    installer.succeed("printf '%s\\n' 11111111111111111111111111111111 > /mnt/persist/etc/machine-id")
    installer.succeed("chmod 0444 /mnt/persist/etc/machine-id")
    installer.succeed("nixos-install --root /mnt --system ${installed.config.system.build.toplevel} --no-channel-copy --no-root-passwd", timeout=3600)
    installer.succeed("test -e /mnt/boot/EFI/BOOT/BOOTX64.EFI")
    installer.succeed("sync -f /mnt/nix/store")
    installer.shutdown()

    variables = Path(tempfile.mkdtemp()) / "efi-vars.fd"
    shutil.copyfile("${pkgs.OVMF.variables}", variables)
    command = shlex.split("${qemuCommon.qemuBinary pkgs.qemu_test}") + [
        "-m", "4096", "-smp", "2",
        "-drive", f"file={installer.state_dir}/empty0.qcow2,if=none,id=installed,format=qcow2",
        "-device", "virtio-blk-pci,drive=installed,serial=reconstruction",
        "-drive", "if=pflash,format=raw,unit=0,readonly=on,file=${pkgs.OVMF.firmware}",
        "-drive", f"if=pflash,format=raw,unit=1,file={variables}",
    ]
    # Deliberately no host store, 9p mount, kernel or initrd supplied by QEMU.
    machine = create_machine(start_command=shlex.join(command), name="reconstructed")
    driver.machines_qemu.append(machine)
    machine.start(allow_reboot=True)
    machine.wait_for_unit("multi-user.target", timeout=600)
    machine.wait_for_unit("home-manager-${username}.service", timeout=600)
    machine.succeed("test $(readlink -f /run/current-system) = ${installed.config.system.build.toplevel}")
    machine.succeed("test $(cat /etc/machine-id) = 11111111111111111111111111111111")
    machine.succeed("test -z \"$(findmnt -rn -t 9p,overlay)\"")
    for path in ["/nix", "/home", "/var", "/persist", "/var/lib/nixos-optimization"]:
        machine.succeed(f"mountpoint {path}")
    machine.succeed("test \"$(getent shadow ${username} | cut -d: -f2)\" = \"$(cat /persist/secrets/${username}-password-hash)\"")
    machine.succeed("logger -t reconstruction persistent-journal-probe")
    machine.succeed("journalctl --sync")
    machine.succeed("touch /reconstruction-local /persist/reconstruction-persistent")
    machine.reboot()
    machine.wait_for_unit("multi-user.target", timeout=600)
    machine.succeed("test ! -e /reconstruction-local && test -e /persist/reconstruction-persistent")
    machine.succeed("journalctl --no-pager --grep=persistent-journal-probe")
    root_id = machine.succeed("btrfs subvolume show / | sed -n 's/.*Subvolume ID:[[:space:]]*//p'").strip()
    resets = machine.succeed("grep -c 'RESET complete' /persist/ephemeral-root-reset.log").strip()
    assert int(resets) >= 2
    machine.succeed("touch /reconstruction-recovery-local")
    entries = json.loads(machine.succeed("bootctl list --json=short"))
    recovery = [entry["id"] for entry in entries if "persistent-root" in entry["id"]]
    assert recovery
    machine.succeed(f"bootctl set-oneshot {shlex.quote(recovery[0])}")
    machine.reboot()
    machine.wait_for_unit("multi-user.target", timeout=600)
    machine.succeed("test -e /reconstruction-recovery-local && test -e /persist/reconstruction-persistent")
    assert machine.succeed("btrfs subvolume show / | sed -n 's/.*Subvolume ID:[[:space:]]*//p'").strip() == root_id
    assert machine.succeed("grep -c 'RESET complete' /persist/ephemeral-root-reset.log").strip() == resets
    machine.succeed("test $(cat /etc/machine-id) = 11111111111111111111111111111111")
    machine.succeed("test -z \"$(systemctl --failed --no-legend --plain)\"")
    machine.reboot()
    machine.wait_for_unit("multi-user.target", timeout=600)
    machine.succeed("test ! -e /reconstruction-recovery-local && test -e /persist/reconstruction-persistent")
    assert int(machine.succeed("grep -c 'RESET complete' /persist/ephemeral-root-reset.log").strip()) == int(resets) + 1
    machine.shutdown()
    installer.start()
    installer.wait_for_unit("multi-user.target")
    installer.succeed("mkdir -p /mnt/reconstruction-inspect")
    installer.succeed("mount -t btrfs -o ro,rescue=nologreplay,subvolid=5 ${diskDevice}-part3 /mnt/reconstruction-inspect")
    for name in ["@root", "@home", "@var", "@nix", "@persist", "@optimization", "@snapshots"]:
        installer.succeed(f"btrfs subvolume show /mnt/reconstruction-inspect/{name}")
    installer.succeed("test $(cat /mnt/reconstruction-inspect/@persist/etc/machine-id) = 11111111111111111111111111111111")
    installer.succeed("umount /mnt/reconstruction-inspect")
  '';
}
