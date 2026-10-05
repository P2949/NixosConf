{ pkgs }:

let
  diskDevice = "/dev/disk/by-id/virtio-impermanence-root";
in
pkgs.testers.runNixOSTest {
  name = "impermanence-root-safety";

  nodes.machine =
    { pkgs, ... }:
    {
      imports = [
        ../modules/storage/ephemeral-btrfs-root.nix
      ];

      virtualisation = {
        emptyDiskImages = [
          {
            size = 4096;
            driveConfig.deviceExtraOpts.serial = "impermanence-root";
          }
        ];

        memorySize = 1024;
        cores = 2;
      };

      environment.systemPackages = [
        pkgs.btrfs-progs
        pkgs.coreutils
        pkgs.util-linux
      ];

      specialisation.ephemeral.configuration = {
        virtualisation = {
          useDefaultFilesystems = false;

          fileSystems."/" = {
            device = diskDevice;
            fsType = "btrfs";
            options = [
              "subvol=@root"
              "compress=zstd:1"
              "noatime"
            ];
          };
        };

        boot.initrd.systemd.enable = true;
        boot.ephemeralBtrfsRoot.enable = true;
      };

      system.stateVersion = "26.05";
    };

  testScript =
    { nodes, ... }:

    let
      resetScript = pkgs.writeShellScript "ephemeral-root-reset-safety" nodes.machine.specialisation.ephemeral.configuration.boot.initrd.systemd.services.ephemeral-root-reset.script;
      nestedResetScript = pkgs.writeShellScript "ephemeral-root-reset-nested-log" (
        builtins.replaceStrings
          [ "log_relative=${pkgs.lib.escapeShellArg "ephemeral-root-reset.log"}" ]
          [ "log_relative=${pkgs.lib.escapeShellArg "logs/reset.log"}" ]
          nodes.machine.specialisation.ephemeral.configuration.boot.initrd.systemd.services.ephemeral-root-reset.script
      );
    in
    ''
      import re
      import shlex

      top = "/mnt/impermanence-root"
      log_path = top + "/@persist/ephemeral-root-reset.log"
      machine.start()
      machine.wait_for_unit("multi-user.target")
      machine.succeed("mkdir -p " + top)

      def mount_disk():
          machine.succeed("mount -t btrfs -o subvolid=5 ${diskDevice} " + top)

      def create_subvolume(relative):
          machine.succeed("btrfs subvolume create " + shlex.quote(top + "/" + relative))

      def sentinel(relative):
          path = shlex.quote(top + "/" + relative)
          machine.succeed("printf '%s\\n' preserve-this-data > " + path)

      def snapshot():
          # Ignore transaction generation and the intentional diagnostic log,
          # but compare every subvolume ID/UUID, path, file digest and symlink.
          identities = machine.succeed(
              "btrfs subvolume list -p -u " + top
              + " | sed -E 's/ gen [0-9]+ / /' | sort"
          )
          entries = machine.succeed(
              "find " + top + " -mindepth 1 ! -path " + log_path
              + " -printf '%P %y %m %l\\n' | sort"
          )
          contents = machine.succeed(
              "find " + top + " -type f ! -path " + log_path
              + " -exec sha256sum {} + | sort"
          )
          return identities, entries, contents

      cases = [
          ("unknown-root-child", True, "absent", "unknown", "unknown root descendant"),
          ("unknown-root-child-with-staging", True, "empty", "unknown", "unknown root descendant"),
          ("unknown-grandchild", True, "absent", "grandchild", "unexpected descendants"),
          ("path-delimiter-in-name", True, "empty", "path-delimiter", "unknown root descendant"),
          ("both-missing", False, "absent", "normal", "neither @root nor @root-next exists"),
          ("invalid-root-directory", True, "empty", "directory", "@root exists but is not a Btrfs subvolume"),
          ("invalid-root-symlink", True, "empty", "symlink", "@root exists but is not a Btrfs subvolume"),
          ("missing-persistence", True, "empty", "no-persist", "persistence subvolume is missing"),
          ("invalid-persistence", True, "empty", "persist-directory", "persistence path is not a Btrfs subvolume"),
          ("sysroot-mounted", True, "empty", "mounted", "/sysroot is already mounted"),
      ]
      for kind in ("symlink", "broken-symlink", "directory", "fifo", "hardlink"):
          reason = "must not have hard links" if kind == "hardlink" else "must be a regular file without aliases"
          cases.append(("log-" + kind, True, "empty", "log-" + kind, reason))
      for kind in ("symlink", "file"):
          cases.append(("log-parent-" + kind, True, "empty", "parent-" + kind, "unsafe reset log parent"))
      for root_present in (False, True):
          for staging in ("child", "file", "dotfile", "directory", "symlink", "plain-directory", "alias", "broken-alias"):
              reason = (
                  "unexpected descendants" if staging == "child"
                  else "not a Btrfs subvolume" if staging in ("plain-directory", "alias", "broken-alias")
                  else "unexpected directory entries"
              )
              cases.append((f"staging-{staging}-root-{root_present}", root_present, staging, "normal", reason))

      for name, root_present, staging, root_kind, reason in cases:
          with subtest(name):
              machine.succeed("mkfs.btrfs -f -L impermanence-safety ${diskDevice}")
              mount_disk()
              create_subvolume("@keep")
              sentinel("@keep/sentinel")
              if root_kind != "no-persist":
                  if root_kind == "persist-directory":
                      machine.succeed("mkdir " + top + "/@persist")
                  else:
                      create_subvolume("@persist")
                  sentinel("@persist/persist-sentinel")

              if root_present:
                  if root_kind == "directory":
                      machine.succeed("mkdir " + top + "/@root")
                  elif root_kind == "symlink":
                      machine.succeed("ln -s @keep " + top + "/@root")
                  else:
                      create_subvolume("@root")
                  sentinel("@root/root-sentinel")
                  if root_kind == "unknown":
                      create_subvolume("@root/important-data")
                      sentinel("@root/important-data/sentinel")
                  elif root_kind == "grandchild":
                      create_subvolume("@root/tmp")
                      create_subvolume("@root/tmp/important-data")
                      sentinel("@root/tmp/important-data/sentinel")
                  elif root_kind == "path-delimiter":
                      create_subvolume("@root/tmp")
                      sentinel("@root/tmp/sentinel")
                      machine.succeed("mkdir -p " + shlex.quote(top + "/@root/important path @root"))
                      create_subvolume("@root/important path @root/tmp")
                      sentinel("@root/important path @root/tmp/sentinel")

              if staging == "plain-directory":
                  machine.succeed("mkdir " + top + "/@root-next")
                  sentinel("@root-next/sentinel")
              elif staging in ("alias", "broken-alias"):
                  target = "@keep" if staging == "alias" else "missing"
                  machine.succeed("ln -s " + target + " " + top + "/@root-next")
              elif staging != "absent":
                  create_subvolume("@root-next")
                  if staging == "child":
                      create_subvolume("@root-next/important-data")
                      sentinel("@root-next/important-data/sentinel")
                  elif staging in ("file", "dotfile"):
                      sentinel("@root-next/" + (".sentinel" if staging == "dotfile" else "sentinel"))
                  elif staging == "directory":
                      machine.succeed("mkdir " + top + "/@root-next/data")
                  elif staging == "symlink":
                      machine.succeed("ln -s missing " + top + "/@root-next/data")

              if root_kind == "parent-symlink":
                  machine.succeed("ln -s ../@keep " + top + "/@persist/logs")
              elif root_kind == "parent-file":
                  sentinel("@persist/logs")
              log_metadata = None
              if root_kind.startswith("log-"):
                  if root_kind in ("log-symlink", "log-broken-symlink"):
                      target = "persist-sentinel" if root_kind == "log-symlink" else "missing"
                      machine.succeed("ln -s " + target + " " + log_path)
                  elif root_kind == "log-hardlink":
                      machine.succeed("ln " + top + "/@persist/persist-sentinel " + log_path)
                  elif root_kind == "log-directory":
                      machine.succeed("mkdir " + log_path)
                  else:
                      machine.succeed("mkfifo " + log_path)
                  log_metadata = machine.succeed("stat -c '%F %a %h' " + log_path)
              before = snapshot()
              if root_kind == "mounted":
                  machine.succeed("mkdir -p /sysroot")
                  machine.succeed("mount --bind " + top + "/@root /sysroot")
              machine.succeed("umount " + top)
              script = "${nestedResetScript}" if root_kind.startswith("parent-") else "${resetScript}"
              output = machine.fail(script + " 2>&1")
              assert reason in output, output
              if root_kind == "mounted":
                  machine.succeed("umount /sysroot")
              machine.succeed("! mountpoint -q /run/ephemeral-root-btrfs")
              mount_disk()
              assert snapshot() == before, name + ": filesystem changed after refusal"

              if log_metadata is not None:
                  assert machine.succeed("stat -c '%F %a %h' " + log_path) == log_metadata
              elif not root_kind.startswith("parent-") and root_kind not in ("mounted", "no-persist", "persist-directory"):
                  reset_log = machine.succeed("cat " + log_path)
                  assert reason in reset_log, reset_log
                  messages = re.findall(r"^\[[^]]+\] (.*)$", reset_log, re.MULTILINE)
                  assert sum(message.startswith("BEGIN boot_id=") for message in messages) == 1
                  assert not any(message in ("RESET complete", "RECOVERY complete") for message in messages)
                  machine.succeed("test \"$(stat -c %a " + log_path + ")\" = 600")
              else:
                  machine.succeed("test ! -e " + log_path)
              machine.succeed("umount " + top)

      with subtest("nested-log-positive-control"):
          machine.succeed("mkfs.btrfs -f -L impermanence-safety ${diskDevice}")
          mount_disk()
          create_subvolume("@persist")
          create_subvolume("@root")
          sentinel("@persist/persist-sentinel")
          sentinel("@root/root-sentinel")
          old_root = machine.succeed("btrfs subvolume show " + top + "/@root")
          machine.succeed("umount " + top)
          machine.succeed("${nestedResetScript}")
          machine.succeed("! mountpoint -q /run/ephemeral-root-btrfs")
          mount_disk()
          assert machine.succeed("btrfs subvolume show " + top + "/@root") != old_root
          machine.succeed("test ! -e " + top + "/@root/root-sentinel")
          machine.succeed("grep -qx preserve-this-data " + top + "/@persist/persist-sentinel")
          nested_log = top + "/@persist/logs/reset.log"
          machine.succeed("test -f " + nested_log + " && test ! -L " + nested_log)
          machine.succeed("test $(stat -c %a " + nested_log + ") = 600")
          assert "RESET complete" in machine.succeed("cat " + nested_log)
          machine.succeed("test ! -e " + top + "/@root-next")
          machine.succeed("umount " + top)
    '';
}
