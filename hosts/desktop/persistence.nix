{
  config,
  lib,
  pkgs,
  username,
  ...
}:

{
  imports = [ ../../modules/storage/ephemeral-application-state ];

  config = {

    workstation.ephemeralApplicationState = {
      enable = true;
      user = username;
      paths = import ../../home/p2949/persistence/ephemeral-directories.nix;
      files = import ../../home/p2949/persistence/ephemeral-files.nix;
    };

    environment.persistence."/persist" = {
      hideMounts = true;

      files = [
        "/etc/machine-id"
        {
          file = "/var/lib/systemd/random-seed";
          parentDirectory.mode = "0755";
        }
      ];

      directories = [
        {
          directory = "/etc/nixos";
          user = username;
          group = "users";
          mode = "0755";
        }

        {
          directory = "/etc/NetworkManager/system-connections";
          mode = "0700";
        }

        # Stable account allocation, Bluetooth pairing and scrub history.
        "/var/lib/nixos"
        {
          directory = "/var/lib/bluetooth";
          mode = "0700";
        }
        "/var/lib/btrfs"
        # NetworkManager atomically creates its identity key, so persist the
        # enclosing directory and discard its known disposable children at boot.
        "/var/lib/NetworkManager"
      ];
    };

    # Logs/coredumps live on the reset root; journal storage uses runtime memory.
    services.journald.storage = "volatile";

    systemd.tmpfiles.rules = lib.mkIf config.boot.ephemeralBtrfsRoot.enable [
      "r! /var/lib/NetworkManager/*.lease - - - -"
      "r! /var/lib/NetworkManager/seen-bssids - - - -"
      "r! /var/lib/NetworkManager/timestamps - - - -"
    ];

    # Upstream tmpfiles creates these as Btrfs subvolumes. Once /var is inside
    # @root they would (correctly) trip the reset module's descendant guard.
    # Keep the upstream rules but create ordinary directories at these paths.
    environment.etc =
      lib.genAttrs [ "tmpfiles.d/portables.conf" "tmpfiles.d/systemd-nspawn.conf" "tmpfiles.d/tmp.conf" ]
        (name: {
          source = pkgs.runCommand "granular-${builtins.baseNameOf name}" { } ''
            sed -E '/^[qQ] \/(var\/lib\/(machines|portables)|var\/tmp)( |$)/s/^[qQ]/d/' \
              ${config.systemd.package}/example/${name} > "$out"
          '';
        });

    assertions = [
      {
        assertion = !(config.fileSystems ? "/home");
        message = "Granular Impermanence requires /home to live inside the ephemeral root.";
      }
      {
        assertion = !(config.fileSystems ? "/var");
        message = "Granular Impermanence requires /var to live inside the ephemeral root.";
      }
      {
        assertion =
          config.fileSystems ? "/var/lib/nixos-optimization"
          && lib.elem "subvol=@optimization" config.fileSystems."/var/lib/nixos-optimization".options;
        message = "Granular Impermanence must retain the dedicated @optimization mount.";
      }
    ];
  };
}
