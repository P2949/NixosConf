{
  inputs,
  pkgs,
}:

let
  diskDevice = "/dev/disk/by-id/virtio-impermanence-root";
in
pkgs.testers.runNixOSTest {
  name = "impermanence-root-a";

  nodes.machine =
    { pkgs, ... }:
    {
      imports = [
        inputs.impermanence.nixosModules.impermanence
        inputs.home-manager.nixosModules.home-manager
        ../modules/storage/ephemeral-btrfs-root.nix
      ];

      virtualisation = {
        emptyDiskImages = [
          {
            size = 4096;
            driveConfig.deviceExtraOpts.serial = "impermanence-root";
          }
        ];

        useBootLoader = true;
        mountHostNixStore = true;
        useEFIBoot = true;

        memorySize = 2048;
        cores = 2;
      };

      boot.loader.systemd-boot.enable = true;
      boot.loader.efi.canTouchEfiVariables = true;

      boot.initrd.systemd = {
        enable = true;
        emergencyAccess = true;
      };

      environment.systemPackages = [
        pkgs.btrfs-progs
        pkgs.openssl
      ];

      specialisation.ephemeral.configuration = {
        virtualisation = {
          useDefaultFilesystems = false;

          fileSystems = {
            "/" = {
              device = diskDevice;
              fsType = "btrfs";
              options = [
                "subvol=@root"
                "compress=zstd:1"
                "noatime"
              ];
            };

            "/persist" = {
              device = diskDevice;
              fsType = "btrfs";
              options = [
                "subvol=@persist"
                "compress=zstd:1"
                "noatime"
              ];
              neededForBoot = true;
            };

            "/var" = {
              device = diskDevice;
              fsType = "btrfs";
              options = [
                "subvol=@var"
                "compress=zstd:1"
                "noatime"
              ];
            };

            "/home" = {
              device = diskDevice;
              fsType = "btrfs";
              options = [
                "subvol=@home"
                "compress=zstd:1"
                "noatime"
              ];
            };
          };
        };

        boot.ephemeralBtrfsRoot.enable = true;

        environment.persistence."/persist" = {
          hideMounts = true;

          directories = [
            {
              directory = "/etc/nixos";
              user = "tester";
              group = "users";
              mode = "0755";
            }

            {
              directory = "/etc/NetworkManager/system-connections";
              mode = "0700";
            }
          ];
        };

        networking.networkmanager.enable = true;

        users.users.tester = {
          isNormalUser = true;
          uid = 1000;
          createHome = true;
          shell = pkgs.bashInteractive;
          hashedPasswordFile = "/persist/secrets/tester-password-hash";
        };

        home-manager = {
          useGlobalPkgs = true;
          useUserPackages = true;
          verbose = true;

          users.tester = {
            home.username = "tester";
            home.homeDirectory = "/home/tester";
            home.stateVersion = "26.05";

            home.activationGenerateGcRoot = false;
          };
        };
      };

      system.stateVersion = "26.05";
    };

  testScript =
    { nodes, ... }:

    let
      ephemeralSystem = nodes.machine.specialisation.ephemeral.configuration.system.build.toplevel;
    in
    ''
      machine.start(allow_reboot=True)
      machine.wait_for_unit("multi-user.target")

      machine.succeed("mkfs.btrfs -f -L impermanence-test ${diskDevice}")
      machine.succeed("mkdir -p /mnt/impermanence-root")
      machine.succeed("mount -t btrfs -o subvolid=5 ${diskDevice} /mnt/impermanence-root")

      machine.succeed("btrfs subvolume create /mnt/impermanence-root/@root")
      machine.succeed("btrfs subvolume create /mnt/impermanence-root/@root/tmp")
      machine.succeed("btrfs subvolume create /mnt/impermanence-root/@root/srv")
      machine.succeed("chmod 1777 /mnt/impermanence-root/@root/tmp")

      machine.succeed("btrfs subvolume create /mnt/impermanence-root/@persist")
      machine.succeed("btrfs subvolume create /mnt/impermanence-root/@var")
      machine.succeed("btrfs subvolume create /mnt/impermanence-root/@home")
      machine.succeed("mkdir -p /mnt/impermanence-root/@home/tester")
      machine.succeed("chown 1000:100 /mnt/impermanence-root/@home/tester")
      machine.succeed("chmod 0755 /mnt/impermanence-root/@home/tester")

      machine.succeed("mkdir -p /mnt/impermanence-root/@persist/secrets")
      machine.succeed("mkdir -p /mnt/impermanence-root/@persist/etc/nixos")
      machine.succeed("mkdir -p /mnt/impermanence-root/@persist/etc/NetworkManager/system-connections")

      machine.succeed("openssl passwd -6 -salt nixos-test test > /mnt/impermanence-root/@persist/secrets/tester-password-hash")
      machine.succeed("chmod 0600 /mnt/impermanence-root/@persist/secrets/tester-password-hash")

      machine.succeed("chown 1000:100 /mnt/impermanence-root/@persist/etc/nixos")
      machine.succeed("chmod 0755 /mnt/impermanence-root/@persist/etc/nixos")
      machine.succeed("chmod 0700 /mnt/impermanence-root/@persist/etc/NetworkManager/system-connections")

      machine.succeed("echo disposable > /mnt/impermanence-root/@root/root-sentinel")
      machine.succeed("echo persistent > /mnt/impermanence-root/@persist/persist-sentinel")
      machine.succeed("echo repository-state > /mnt/impermanence-root/@persist/etc/nixos/persist-sentinel")
      machine.succeed("echo persistent-var > /mnt/impermanence-root/@var/var-sentinel")
      machine.succeed("echo persistent-home > /mnt/impermanence-root/@home/home-sentinel")

      machine.succeed("umount /mnt/impermanence-root")

      machine.succeed("${ephemeralSystem}/bin/switch-to-configuration boot")

      def arm_ephemeral_boot():
          machine.log(machine.succeed("cat /boot/loader/loader.conf"))
          machine.log(machine.succeed("bootctl list --no-pager"))

          machine.log(
              machine.succeed(
                  "for entry in /boot/loader/entries/*.conf; do "
                  "echo === $entry; "
                  "grep -E '^(title|linux|initrd|options) ' \"$entry\"; "
                  "done"
              )
          )

          machine.succeed(
              "entry=$(grep -lF -- "
              "'${ephemeralSystem}/init' "
              "/boot/loader/entries/*.conf | head -n1); "
              "test -n \"$entry\"; "
              "id=$(basename \"$entry\"); "
              "grep -q '^default ' /boot/loader/loader.conf; "
              "sed -i \"s|^default .*|default $id|\" "
              "/boot/loader/loader.conf; "
              "grep -Fx \"default $id\" "
              "/boot/loader/loader.conf"
          )

          machine.succeed("sync")
          machine.log(machine.succeed("cat /boot/loader/loader.conf"))
          machine.log(machine.succeed("bootctl list --no-pager"))

      arm_ephemeral_boot()

      machine.crash()
      machine.start(allow_reboot=True)

      def validate_boot(expected_reset_count):
          machine.wait_for_unit("multi-user.target")

          machine.log(
              machine.succeed("readlink -f /run/current-system")
          )
          machine.log(
              machine.succeed(
                  "findmnt -rn -o SOURCE,FSTYPE,OPTIONS /"
              )
          )
          machine.log(
              machine.succeed(
                  "test ! -e /persist/ephemeral-root-reset.log "
                  "|| cat /persist/ephemeral-root-reset.log"
              )
          )

          # Prove that the test really reached the configuration under test
          # before making any higher-level service assertions.
          machine.succeed(
              "test \"$(readlink -f /run/current-system)\" "
              "= '${ephemeralSystem}'"
          )

          # Prove that the real root is the Btrfs ephemeral root rather
          # than the bootstrap VM's ext4 filesystem.
          machine.succeed(
              "test \"$(findmnt -rn -o FSTYPE /)\" = btrfs"
          )
          machine.succeed(
              "findmnt -rn -o OPTIONS / | grep -q 'subvol=/@root'"
          )

          # The reset service must have run during this boot.
          machine.succeed(
              "test \"$(grep -c 'BEGIN boot_id=' "
              "/persist/ephemeral-root-reset.log)\" "
              f"= {expected_reset_count}"
          )
          machine.succeed(
              "test \"$(grep -c 'RESET complete' "
              "/persist/ephemeral-root-reset.log)\" "
              f"= {expected_reset_count}"
          )

          machine.wait_for_unit("dbus.service")
          machine.wait_for_unit("systemd-logind.service")
          machine.wait_for_unit("NetworkManager.service")

          machine.wait_until_succeeds(
              "systemctl is-active --quiet home-manager-tester.service "
              "|| systemctl is-failed --quiet home-manager-tester.service"
          )
          machine.log(
              machine.succeed(
                  "systemctl status --no-pager -l "
                  "home-manager-tester.service || true"
              )
          )
          machine.log(
              machine.succeed(
                  "journalctl -b -u home-manager-tester.service "
                  "--no-pager -o cat || true"
              )
          )
          machine.log(
              machine.succeed(
                  "journalctl -b -t hm-activate-tester "
                  "--no-pager -o cat || true"
              )
          )
          machine.log(
              machine.succeed(
                  "id tester; "
                  "stat -c '%U:%G %a %n' /home /home/tester; "
                  "find /home/tester -maxdepth 4 "
                  "-printf '%M %u:%g %p -> %l\\n' "
                  "2>/dev/null | sort; "
                  "find /nix/var/nix/profiles/per-user/tester -maxdepth 2 "
                  "-printf '%M %u:%g %p -> %l\\n' "
                  "2>/dev/null | sort || true"
              )
          )
          machine.succeed(
              "systemctl is-active --quiet "
              "home-manager-tester.service"
          )

          machine.succeed("test ! -e /root-sentinel")
          machine.succeed("test -f /persist/persist-sentinel")
          machine.succeed("test -f /etc/nixos/persist-sentinel")
          machine.succeed("test -f /var/var-sentinel")
          machine.succeed("test -f /home/home-sentinel")

          machine.succeed("mkdir /tmp/ephemeral-root-probe")
          machine.succeed("rmdir /tmp/ephemeral-root-probe")
          machine.succeed("test \"$(stat -c %a /tmp)\" = 1777")

          machine.succeed(
              "test \"$(getent shadow tester | cut -d: -f2)\" = "
              "\"$(cat /persist/secrets/tester-password-hash)\""
          )

          machine.succeed("test ! -e /persist/etc/machine-id")

      validate_boot(1)

      machine.succeed("echo disposable-second > /root-sentinel")
      machine.succeed("echo second >> /persist/persist-sentinel")
      arm_ephemeral_boot()
      machine.reboot()

      validate_boot(2)

      machine.succeed("echo disposable-third > /root-sentinel")
      machine.succeed("echo third >> /persist/persist-sentinel")
      arm_ephemeral_boot()
      machine.reboot()

      validate_boot(3)

      machine.succeed(
          "test \"$(grep -c 'RESET complete' /persist/ephemeral-root-reset.log)\" = 3"
      )
      machine.succeed(
          "test \"$(grep 'BEGIN boot_id=' "
          "/persist/ephemeral-root-reset.log "
          "| sed -E 's/.*boot_id=([^ ]+).*/\\1/' "
          "| sort -u | wc -l)\" = 3"
      )
    '';
}
