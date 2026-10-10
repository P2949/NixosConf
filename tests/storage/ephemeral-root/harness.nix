{
  inputs,
  pkgs,
  persistMachineId ? false,
  recovery ? false,
  persistentFallback ? false,
  granular ? false,
}:

let
  diskDevice = "/dev/disk/by-id/virtio-impermanence-root";
in
assert !persistentFallback || persistMachineId;
pkgs.testers.runNixOSTest {
  name =
    if granular then
      "granular-impermanence"
    else if persistentFallback then
      "impermanence-root-fallback"
    else if recovery then
      "impermanence-root-recovery"
    else if persistMachineId then
      "impermanence-root-b"
    else
      "impermanence-root-a";

  nodes.machine =
    { pkgs, ... }:
    let
      btrfsConfiguration = {
        imports = pkgs.lib.optionals granular [ ../../../hosts/desktop/persistence.nix ];
        _module.args.username = "tester";
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

          }
          // pkgs.lib.optionalAttrs (!granular) {
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
          }
          // pkgs.lib.optionalAttrs granular {
            "/var/lib/nixos-optimization" = {
              device = diskDevice;
              fsType = "btrfs";
              options = [ "subvol=@optimization" ];
            };
          };
        };

        boot.ephemeralBtrfsRoot.enable = true;

        environment.persistence."/persist" =
          if granular then
            {
              files = [ "/var/lib/impermanence-fixture" ];
            }
          else
            {
              hideMounts = true;

              files = pkgs.lib.optional persistMachineId "/etc/machine-id";

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

        services.journald.storage = pkgs.lib.mkIf (persistMachineId && !granular) "persistent";

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
            imports = pkgs.lib.optionals granular [ ../../../home/p2949/persistence/default.nix ];
            home.username = "tester";
            home.homeDirectory = "/home/tester";
            home.stateVersion = "26.05";

            home.activationGenerateGcRoot = false;
            home.file.".config/reconstruction-proof".text = "declarative\n";
          };
        };
      };
    in
    {
      imports = [
        inputs.impermanence.nixosModules.impermanence
        inputs.home-manager.nixosModules.home-manager
        ../../../modules/storage/ephemeral-btrfs-root
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
      ]
      ++ pkgs.lib.optionals granular [ pkgs.git ];

      specialisation = {
        ephemeral.configuration = btrfsConfiguration;
      }
      // pkgs.lib.optionalAttrs persistentFallback {
        persistent-root.configuration = {
          imports = [ btrfsConfiguration ];
          boot.ephemeralBtrfsRoot.enable = pkgs.lib.mkForce false;
        };
      };

      system.stateVersion = "26.05";
    };

  testScript =
    { nodes, ... }:

    let
      ephemeralSystem = nodes.machine.specialisation.ephemeral.configuration.system.build.toplevel;
      fallbackSystem = nodes.machine.specialisation.persistent-root.configuration.system.build.toplevel;
    in
    ''
      import re

      recovery = ${if recovery then "True" else "False"}
      persist_machine_id = ${if persistMachineId then "True" else "False"}
      granular = ${if granular then "True" else "False"}
      machine_ids = []
      ephemeral_paths = [
          "/etc/granular-proof", "/root/granular-proof", "/tmp/granular-proof",
          "/srv/granular-proof", "/usr/local/granular-proof",
          "/home/tester/.cache/granular-proof", "/home/tester/undeclared/granular-proof",
          "/var/cache/granular-proof", "/var/tmp/granular-proof",
          "/var/lib/undeclared-service/granular-proof",
      ]
      persistent_paths = [
          "/home/tester/Documents/granular-proof", "/home/tester/.ssh/granular-proof",
          "/var/lib/nixos/granular-proof", "/var/lib/impermanence-fixture",
          "/var/lib/nixos-optimization/granular-proof", "/persist/granular-proof",
          "/etc/NetworkManager/system-connections/granular-proof",
      ]
      application_cache_paths = [
          "/home/tester/Development/Unity/VR-AR-project-2/Temp/granular-proof",
          "/home/tester/Development/Unreal/Projects/AI_Gavin_Project/Intermediate/granular-proof",
          "/home/tester/.codex/cache/granular-proof",
          "/home/tester/.config/mozilla/firefox/y34aofre.default/cache2/granular-proof",
          "/home/tester/.config/Code/GPUCache/granular-proof",
          "/home/tester/.config/unityhub/Cache/granular-proof",
          "/home/tester/.config/Epic/UnrealEngine/5.8/Intermediate/granular-proof",
          "/home/tester/.local/share/Steam/appcache/granular-proof",
      ]
      if granular:
          ephemeral_paths += application_cache_paths
          ephemeral_paths += ["/home/tester/.codex/models_cache.json", "/home/tester/.codex/logs_2.sqlite"]
          ephemeral_paths += ["/var/lib/NetworkManager/granular-test.lease"]
          persistent_paths += ["/var/lib/NetworkManager/granular-proof"]
          persistent_paths += [
              "/home/tester/.local/share/Steam/steamapps/shadercache/granular-proof",
              "/home/tester/.config/Epic/UnrealEngine/Common/DerivedDataCache/granular-proof",
          ]

      machine.start(allow_reboot=True)
      machine.wait_for_unit("multi-user.target")

      machine.succeed("mkfs.btrfs -f -L impermanence-test ${diskDevice}")
      machine.succeed("mkdir -p /mnt/impermanence-root")
      machine.succeed("mount -t btrfs -o subvolid=5 ${diskDevice} /mnt/impermanence-root")

      if recovery:
          machine.succeed("btrfs subvolume create /mnt/impermanence-root/@root-next")
          staging_identity = machine.succeed(
              "btrfs subvolume show /mnt/impermanence-root/@root-next "
              "| grep -E '^\\s*(UUID|Subvolume ID):'"
          )
      else:
          machine.succeed("btrfs subvolume create /mnt/impermanence-root/@root")
          machine.succeed("btrfs subvolume create /mnt/impermanence-root/@root/tmp")
          machine.succeed("btrfs subvolume create /mnt/impermanence-root/@root/srv")
          machine.succeed("chmod 1777 /mnt/impermanence-root/@root/tmp")
          machine.succeed("echo disposable > /mnt/impermanence-root/@root/root-sentinel")

      machine.succeed("btrfs subvolume create /mnt/impermanence-root/@persist")
      if granular:
          machine.succeed("btrfs subvolume create /mnt/impermanence-root/@optimization")
      else:
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

      machine.succeed("echo persistent > /mnt/impermanence-root/@persist/persist-sentinel")
      machine.succeed("echo repository-state > /mnt/impermanence-root/@persist/etc/nixos/persist-sentinel")
      if granular:
          machine.succeed("install -d -m 0700 -o 1000 -g 100 /mnt/impermanence-root/@persist/home/tester /mnt/impermanence-root/@persist/home/tester/.config /mnt/impermanence-root/@persist/home/tester/.config/git")
          machine.succeed("printf '[impermanence]\\nfixture = seed\\n' > /mnt/impermanence-root/@persist/home/tester/.config/git/config")
          machine.succeed("chown 1000:100 /mnt/impermanence-root/@persist/home/tester/.config/git/config")
      if not granular:
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

      def validate_boot(expected_boot_count):
          expected_reset_count = expected_boot_count - int(recovery)
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
              f"= {expected_boot_count}"
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
          if not granular:
              machine.succeed("test -f /var/var-sentinel")
              machine.succeed("test -f /home/home-sentinel")
          else:
              for path in ["/home", "/var", "/home/tester/.cache"]:
                  machine.fail(f"mountpoint {path}")
              machine.succeed("findmnt -rn -o OPTIONS /var/lib/nixos-optimization | grep -q 'subvol=/@optimization'")
              machine.succeed("grep -Fx declarative /home/tester/.config/reconstruction-proof")
              for path in ["/home/tester/Documents", "/home/tester/.ssh", "/var/lib/nixos"]:
                  machine.succeed(f"mountpoint {path}")
              for path in ephemeral_paths:
                  machine.succeed(f"test ! -e {path}")
              if expected_boot_count > 1:
                  for path in persistent_paths:
                      machine.succeed(f"grep -Fx persistent {path}")
                  machine.succeed("cmp /var/lib/impermanence-fixture /persist/var/lib/impermanence-fixture")
              # Write through the active user mounts as the actual user, proving
              # that mount ownership permits ordinary application writes.
              machine.succeed("su - tester -c 'printf \"persistent\\n\" > ~/Documents/granular-proof; printf \"persistent\\n\" > ~/.ssh/granular-proof'")
              for path in persistent_paths[2:]:
                  if path.startswith("/home/tester/"):
                      machine.succeed(f"su - tester -c 'mkdir -p $(dirname {path}); printf \"persistent\\n\" > {path}'")
                  else:
                      machine.succeed(f"mkdir -p $(dirname {path}); printf 'persistent\\n' > {path}")
              for path in ephemeral_paths:
                  if path.startswith("/home/tester/"):
                      machine.succeed(f"su - tester -c 'mkdir -p $(dirname {path}); touch {path}'")
                  else:
                      machine.succeed(f"mkdir -p $(dirname {path}); touch {path}")
              machine.succeed("test $(stat -c %a /home/tester/.ssh) = 700")
              machine.succeed("test $(stat -c %U:%G /home/tester/Documents) = tester:users")
              for path in application_cache_paths:
                  # The overlay must come from reset-root storage, not the
                  # persistent application's underlying directory.
                  machine.succeed(f"findmnt -rn -o SOURCE -T {path} | grep -F '/@root/'")
                  machine.succeed(f"su - tester -c 'touch {path}'")
              # Applications must be able to save configuration atomically.
              if expected_boot_count > 1:
                  machine.succeed("grep -Fx second /home/tester/.config/Code/preferences-fixture")
              git_value = machine.succeed("su - tester -c 'git config --global --get impermanence.fixture'").strip()
              assert git_value == ("seed" if expected_boot_count == 1 else "edited"), git_value
              machine.succeed("su - tester -c 'echo first > ~/.config/Code/preferences-fixture; echo second > ~/.config/Code/preferences-fixture.new; mv ~/.config/Code/preferences-fixture.new ~/.config/Code/preferences-fixture'")
              machine.succeed("su - tester -c 'git config --global impermanence.fixture edited'")
              machine.succeed("grep -q edited /persist/home/tester/.config/git/config")
              for path in ["/var/lib/portables", "/var/lib/machines", "/var/tmp"]:
                  machine.fail(f"btrfs subvolume show {path}")

          machine.succeed("mkdir /tmp/ephemeral-root-probe")
          machine.succeed("rmdir /tmp/ephemeral-root-probe")
          machine.succeed("test \"$(stat -c %a /tmp)\" = 1777")

          machine.succeed(
              "test \"$(getent shadow tester | cut -d: -f2)\" = "
              "\"$(cat /persist/secrets/tester-password-hash)\""
          )

          if persist_machine_id:
              machine_id = machine.succeed("cat /etc/machine-id").strip()
              assert re.fullmatch(r"[0-9a-f]{32}", machine_id), machine_id
              machine_ids.append(machine_id)
              machine.succeed("cmp /etc/machine-id /persist/etc/machine-id")
              machine.succeed("test -s /persist/etc/machine-id")
              machine.log(f"Boot {expected_boot_count} machine-id: {machine_id}")
          else:
              machine.succeed("test ! -e /persist/etc/machine-id")
          if persist_machine_id and not granular:
              machine.succeed(f"test -d /var/log/journal/{machine_id}")
              machine.succeed(
                  f"logger -t impermanence-journal 'persistent-boot-{expected_boot_count}'"
              )
              machine.succeed("journalctl --sync")
              for previous_boot in range(1, expected_boot_count + 1):
                  machine.succeed(
                      "journalctl -t impermanence-journal --no-pager -o cat "
                      f"| grep -Fx 'persistent-boot-{previous_boot}'"
                  )

          machine.succeed("mkdir -p /mnt/impermanence-root")
          machine.succeed("mount -t btrfs -o subvolid=5 ${diskDevice} /mnt/impermanence-root")
          machine.succeed("test ! -e /mnt/impermanence-root/@root-next")
          machine.succeed("umount /mnt/impermanence-root")
          machine.succeed(
              "test \"$(grep -c 'RECOVERY complete' "
              "/persist/ephemeral-root-reset.log || true)\" "
              f"= {int(recovery)}"
          )

      validate_boot(1)

      if recovery:
          root_identity = machine.succeed(
              "btrfs subvolume show / | grep -E '^\\s*(UUID|Subvolume ID):'"
          )
          assert root_identity == staging_identity, (root_identity, staging_identity)
          machine.succeed("mkdir -p /mnt/impermanence-root")
          machine.succeed("mount -t btrfs -o subvolid=5 ${diskDevice} /mnt/impermanence-root")
          machine.succeed("test ! -e /mnt/impermanence-root/@root-next")
          machine.succeed("btrfs subvolume create /mnt/impermanence-root/@root-next")
          stale_identity = machine.succeed(
              "btrfs subvolume show /mnt/impermanence-root/@root-next "
              "| grep -E '^\\s*(UUID|Subvolume ID):'"
          )
          machine.succeed("umount /mnt/impermanence-root")

      machine.succeed("echo disposable-second > /root-sentinel")
      machine.succeed("echo second >> /persist/persist-sentinel")
      arm_ephemeral_boot()
      machine.reboot()

      validate_boot(2)

      if recovery:
          new_identity = machine.succeed(
              "btrfs subvolume show / | grep -E '^\\s*(UUID|Subvolume ID):'"
          )
          assert new_identity not in (root_identity, stale_identity), new_identity
          machine.succeed("mount -t btrfs -o subvolid=5 ${diskDevice} /mnt/impermanence-root")
          machine.succeed("test ! -e /mnt/impermanence-root/@root-next")
          machine.succeed("umount /mnt/impermanence-root")
          machine.succeed(
              "grep -Fq 'deleting stale empty staging subvolume @root-next' "
              "/persist/ephemeral-root-reset.log"
          )

      machine.succeed("echo disposable-third > /root-sentinel")
      machine.succeed("echo third >> /persist/persist-sentinel")
      arm_ephemeral_boot()
      machine.reboot()

      validate_boot(3)

      machine.succeed(
          "test \"$(grep -c 'RESET complete' /persist/ephemeral-root-reset.log)\" "
          f"= {3 - int(recovery)}"
      )
      machine.succeed(
          "test \"$(grep 'BEGIN boot_id=' "
          "/persist/ephemeral-root-reset.log "
          "| sed -E 's/.*boot_id=([^ ]+).*/\\1/' "
          "| sort -u | wc -l)\" = 3"
      )

      if persist_machine_id:
          assert len(machine_ids) == 3
          assert len(set(machine_ids)) == 1, machine_ids
    ''
    + pkgs.lib.optionalString persistentFallback ''
      # A real persistent-root boot after three resets must retain both
      # ordinary root state and the same identity/journal backing.
      root_before_fallback = machine.succeed(
          "btrfs subvolume show / | grep -E '^\\s*(UUID|Subvolume ID):'"
      )
      reset_log_before_fallback = machine.succeed("cat /persist/ephemeral-root-reset.log")
      machine.succeed("echo keep-on-recovery > /root-sentinel")
      # The fixture shares only the host store, not persistent /nix metadata.
      # Recreate the profile a real nixos-rebuild boot would install before
      # asking systemd-boot to enumerate generations on the reset root.
      machine.succeed(
          "mkdir -p /nix/var/nix/profiles; "
          "ln -sfn '${fallbackSystem}' /nix/var/nix/profiles/system-1-link; "
          "ln -sfn system-1-link /nix/var/nix/profiles/system"
      )
      machine.succeed("${fallbackSystem}/bin/switch-to-configuration boot")
      machine.succeed(
          "entry=$(grep -lF '${fallbackSystem}/init' /boot/loader/entries/*.conf | head -n1); "
          "test -n \"$entry\"; "
          "id=$(basename \"$entry\"); "
          "sed -i \"s|^default .*|default $id|\" /boot/loader/loader.conf"
      )
      machine.succeed("sync")
      machine.reboot()
      machine.wait_for_unit("multi-user.target")
      machine.succeed("test \"$(readlink -f /run/current-system)\" = '${fallbackSystem}'")
      root_after_fallback = machine.succeed(
          "btrfs subvolume show / | grep -E '^\\s*(UUID|Subvolume ID):'"
      )
      assert root_after_fallback == root_before_fallback
      assert machine.succeed("cat /persist/ephemeral-root-reset.log") == reset_log_before_fallback
      machine.succeed("grep -Fx keep-on-recovery /root-sentinel")
      assert machine.succeed("cat /etc/machine-id").strip() == machine_ids[0]
      machine.succeed("cmp /etc/machine-id /persist/etc/machine-id")
      if not granular:
          for previous_boot in range(1, 4):
              machine.succeed(
                  "journalctl -t impermanence-journal --no-pager -o cat "
                  f"| grep -Fx 'persistent-boot-{previous_boot}'"
              )
      for service in ["NetworkManager", "dbus", "systemd-logind", "home-manager-tester"]:
          machine.wait_for_unit(service + ".service")
      machine.succeed(
          "test \"$(getent shadow tester | cut -d: -f2)\" = "
          "\"$(cat /persist/secrets/tester-password-hash)\""
      )
      machine.succeed("test -z \"$(systemctl --failed --no-legend --plain)\"")
      machine.log("Persistent-root fallback retained root, identity, journal and credentials")
    ''
    + pkgs.lib.optionalString granular ''
      # A second recovery boot must retain ordinary home/var state as well.
      for path in ephemeral_paths:
          machine.succeed(f"test -e {path}")
      for path in persistent_paths:
          machine.succeed(f"grep -Fx persistent {path}")
      machine.reboot()
      machine.wait_for_unit("multi-user.target")
      machine.wait_for_unit("home-manager-tester.service")
      machine.succeed("test \"$(readlink -f /run/current-system)\" = '${fallbackSystem}'")
      assert machine.succeed("cat /persist/ephemeral-root-reset.log") == reset_log_before_fallback
      for path in ephemeral_paths:
          machine.succeed(f"test -e {path}")
      for path in persistent_paths:
          machine.succeed(f"grep -Fx persistent {path}")

      # Installing the recovery-only profile above lets bootloader cleanup
      # remove the normal initrd. Reinstall the normal generation, as a real
      # nixos-rebuild boot does, before selecting it for the return boot.
      machine.succeed("ln -sfn '${ephemeralSystem}' /nix/var/nix/profiles/system-1-link")
      machine.succeed("${ephemeralSystem}/bin/switch-to-configuration boot")
      arm_ephemeral_boot()
      machine.reboot()
      validate_boot(4)
      assert machine.succeed("cat /etc/machine-id").strip() == machine_ids[0]
      machine.succeed("test -z \"$(systemctl --failed --no-legend --plain)\"")
    '';
}
