{
  config,
  inputs,
  lib,
  pkgs,
  username,
  utils,
  ...
}:

let
  timerStamp = "/var/lib/systemd/timers/stamp-minecraft-backup.timer";
  timerStampService = "persist-${utils.escapeSystemdPath "/persist${timerStamp}"}.service";
  baseModDrvs = builtins.attrValues {
    fabric-api = pkgs.fetchurl {
      url = "https://cdn.modrinth.com/data/P7dR8mSH/versions/v2j28coa/fabric-api-0.162.0%2B26.3.jar";
      sha512 = "5ab70908952f1d2346d16b122ca31327f4055db59c279a1bc3c3c581ce359bb541cba15730f55b0727be7c7c4debc4a4412a183c228e0d4dea81c734f7b412ce";
    };

    lithium = pkgs.fetchurl {
      url = "https://cdn.modrinth.com/data/gvQqBUqZ/versions/xS0Q8LSi/lithium-fabric-0.26.2%2Bmc26.3.jar";
      sha512 = "4d7fee66132eedc71feab9390b92c95d7058edbdad0fecfac1d836a2950b97a7ca463afbede61c7ef361ce65e1f927ab9e89dde5bf2e0e0ce486afb5c5dbee40";
    };

    ferritecore = pkgs.fetchurl {
      url = "https://cdn.modrinth.com/data/uXXizFIs/versions/d5ddUdiB/ferritecore-9.0.0-fabric.jar";
      sha512 = "d81fa97e11784c19d42f89c2f433831d007603dd7193cee45fa177e4a6a9c52b384b198586e04a0f7f63cd996fed713322578bde9a8db57e1188854ae5cbe584";
    };

    servercore = pkgs.fetchurl {
      url = "https://cdn.modrinth.com/data/4WWQxlQP/versions/LCG1Bm84/servercore-fabric-1.5.20%2B26.3.jar";
      sha512 = "abe1f806ea587971faf7de826e18b07314a4a9e690f64a4c3a54e7f61c3e6f4792633b13a917252bd8de154cec39da6619110d83799cf533450c5b4cac7a8448";
    };

    spark = pkgs.fetchurl {
      url = "https://cdn.modrinth.com/data/l6YH9Als/versions/e3hsPc1o/spark-1.10.187-fabric.jar";
      sha512 = "c74bf5d5a16b2445ec6ea717eac756412b272a8015e91f91a7bf5a27e6f2f99c4a11878d434510f941f37b0344b3a7d1ba0dd6c34e80642762c48fb6e9a93894";
    };
  };

  chunky = pkgs.fetchurl {
    url = "https://cdn.modrinth.com/data/fALzjamp/versions/4Eotm6ov/Chunky-Fabric-1.5.3.jar";
    sha512 = "b83bfe7b218d0aa6232af977ae741dc1f82b10e50cd12bb759f65cf416b8b62beccb543e587ef0b9670abe03815660f8e091bc6823624d65cf07300571573516";
  };

  baseMods = pkgs.linkFarmFromDrvs "minecraft-survival-mods" baseModDrvs;

  pregenMods = pkgs.linkFarmFromDrvs "minecraft-survival-pregen-mods" (baseModDrvs ++ [ chunky ]);

  minecraftManagementPython = pkgs.python3.withPackages (pythonPackages: [
    pythonPackages.websockets
  ]);

  minecraftManagementClient = pkgs.writeShellApplication {
    name = "minecraft-msmp";
    text = ''
      exec ${minecraftManagementPython}/bin/python3 ${./minecraft-msmp.py} "$@"
    '';
  };

  timerStampSeedService = "minecraft-backup-timer-stamp-seed";
  timerStampSeed = pkgs.writeShellApplication {
    name = "minecraft-backup-timer-stamp-seed";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      stamp=/persist${timerStamp}
      install -d -m 0755 -o root -g root "$(dirname "$stamp")"
      if [[ ! -e "$stamp" && ! -L "$stamp" ]]; then
        (umask 022; set -o noclobber; : > "$stamp")
      fi
      if [[ -L "$stamp" || ! -f "$stamp" \
        || "$(stat -c '%u:%g:%h:%a' "$stamp")" != "0:0:1:644" ]]; then
        echo "Minecraft timer stamp must be a root-owned regular mode 0644 file with one link" >&2
        exit 1
      fi
    '';
  };

  minecraftPrerequisiteCheck = pkgs.writeShellApplication {
    name = "minecraft-prerequisites";
    runtimeInputs = [ pkgs.util-linux ];
    text = ''
      exec ${pkgs.python3}/bin/python3 ${./minecraft-prerequisites.py}
    '';
  };

  minecraftBackupRunner = pkgs.writeShellApplication {
    name = "minecraft-backup";

    runtimeInputs = [
      pkgs.btrfs-progs
    ];

    text = ''
      export MINECRAFT_MSMP_SOURCE=${./minecraft-msmp.py}
      exec ${minecraftManagementPython}/bin/python3 ${./minecraft-backup.py} "$@"
    '';
  };
in
{
  imports = [
    inputs.nix-minecraft.nixosModules.minecraft-servers
  ];

  config = lib.mkMerge [
    {
      nixpkgs.overlays = [
        inputs.nix-minecraft.overlay
      ];

      services.minecraft-servers = {
        enable = true;
        eula = true;
        openFirewall = false;

        dataDir = "/srv/minecraft";
        environmentFile = "/persist/secrets/minecraft-management.env";

        servers.survival = {
          enable = true;
          autoStart = true;
          restart = "always";
          openFirewall = true;

          package = pkgs.fabricServers.fabric-26_3.override {
            loaderVersion = "0.19.5";
            jre_headless = pkgs.openjdk25_headless;
          };

          jvmOpts = [
            "-Xms1G"
            "-Xmx6G"
          ];

          # Access lists are authoritative runtime state on @minecraft.
          whitelist = { };
          operators = { };

          files."config/servercore/optimizations.yml".value = {
            reduce-sync-loads = false;
            cache-ticking-chunks = false;
            optimize-command-blocks = false;
            fast-biome-lookups = false;
            cancel-duplicate-fluid-ticks = false;
          };

          files."config/spark/config.json".value.backgroundProfiler = false;

          extraStartPre = ''
            ${pkgs.coreutils}/bin/chmod 0600 server.properties
            if [[ ! "''${MINECRAFT_MANAGEMENT_SECRET:-}" =~ ^[A-Za-z0-9]{40}$ ]]; then
              echo "Minecraft management secret must be exactly 40 alphanumeric characters" >&2
              exit 1
            fi
          '';

          symlinks.mods = baseMods;

          serverProperties = {
            server-ip = "";
            server-port = 25565;
            max-players = 10;

            online-mode = true;
            white-list = true;
            enforce-whitelist = true;

            view-distance = 12;
            simulation-distance = 8;

            pause-when-empty-seconds = 60;

            management-server-enabled = true;
            management-server-host = "127.0.0.1";
            management-server-port = 25585;
            management-server-secret = "@MINECRAFT_MANAGEMENT_SECRET@";
            management-server-tls-enabled = false;
            management-server-allowed-origins = "";
            status-heartbeat-interval = 0;

            enable-rcon = false;
            use-native-transport = true;
          };
        };
      };

      environment.systemPackages = [
        minecraftManagementClient
        minecraftBackupRunner
      ];

    }
    (lib.mkIf config.services.minecraft-servers.enable {
      assertions = [
        {
          assertion =
            lib.attrNames (lib.filterAttrs (_: server: server.enable) config.services.minecraft-servers.servers)
            == [ "survival" ];
          message = "The local Minecraft backup transaction supports exactly one enabled server (survival); review backup consistency before adding another.";
        }
      ];

      specialisation.minecraft-pregen.configuration = {
        systemd.timers.minecraft-backup = {
          enable = lib.mkForce false;
          wantedBy = lib.mkForce [ ];
        };
        services.minecraft-servers.servers.survival = {
          symlinks.mods = lib.mkForce pregenMods;
          serverProperties."pause-when-empty-seconds" = lib.mkForce (-1);
        };
      };

      system.preSwitchChecks.minecraft = ''${lib.getExe minecraftPrerequisiteCheck} "$@"'';

      systemd.tmpfiles.rules = [
        "d /persist/minecraft-backup 0700 root root -"
        # Do not use RuntimeDirectory cleanup: failed recovery must retain the marker.
        "d /run/minecraft-backup 0700 root root -"
      ];

      # Persist only this timer's authoritative activation timestamp on the reset root.
      environment.persistence."/persist".files = [
        {
          file = timerStamp;
          parentDirectory.mode = "0755";
        }
      ];

      # Seed the backing file before impermanence chooses bind versus symlink.
      # systemd updates the stamp inode without following symlinks on writes.
      systemd.services.${timerStampSeedService} = {
        description = "Prepare the persistent Minecraft timer stamp for bind mounting";
        unitConfig = {
          DefaultDependencies = false;
          RequiresMountsFor = [ "/persist" ];
        };
        before = [ timerStampService ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          ExecStart = lib.getExe timerStampSeed;
          User = "root";
          Group = "root";
          UMask = "0022";
        };
      };
      systemd.services.${lib.removeSuffix ".service" timerStampService} = {
        requires = [ "${timerStampSeedService}.service" ];
        after = [ "${timerStampSeedService}.service" ];
      };

      systemd.timers.minecraft-backup = {
        description = "Periodic Minecraft snapshot backup";
        wantedBy = [ "timers.target" ];
        requires = [ timerStampService ];
        after = [ timerStampService ];
        timerConfig = {
          OnCalendar = "*-*-* 00,06,12,18:00:00 UTC";
          Persistent = true;
          AccuracySec = "5min";
          Unit = "minecraft-backup.service";
        };
      };

      users.users.${username}.extraGroups = [
        "minecraft"
      ];

      systemd.slices.minecraft.sliceConfig = {
        CPUWeight = 50;
        IOWeight = 50;
      };

      systemd.services.minecraft-server-survival = {
        requires = [ "srv-minecraft.mount" ];
        after = [ "srv-minecraft.mount" ];

        unitConfig.ConditionPathIsMountPoint = "/srv/minecraft";

        serviceConfig = {
          Slice = "minecraft.slice";
          Nice = 5;

          MemoryHigh = "8G";
          MemoryMax = "10G";
        };
      };

      systemd.services.minecraft-backup = {
        description = "Create a consistent read-only Minecraft Btrfs snapshot";

        after = [
          "minecraft-server-survival.service"
        ];

        unitConfig.RequiresMountsFor = [
          "/srv/minecraft"
          "/.snapshots"
          "/persist"
        ];

        unitConfig.ConditionPathIsMountPoint = [
          "/srv/minecraft"
          "/.snapshots"
        ];

        serviceConfig = {
          Type = "oneshot";
          TimeoutStartSec = "20min";
          User = "root";
          Group = "root";

          ExecCondition = "${pkgs.systemd}/bin/systemctl is-active --quiet minecraft-server-survival.service";
          ExecStart = "${minecraftBackupRunner}/bin/minecraft-backup";
          ExecStopPost = "${minecraftBackupRunner}/bin/minecraft-backup recover-autosave";

          Slice = "minecraft.slice";
          Nice = 10;
          CPUWeight = 25;
          IOWeight = 25;

          UMask = "0077";

          ProtectSystem = "strict";
          ProtectHome = true;
          PrivateTmp = true;
          ReadOnlyPaths = [ "/srv/minecraft" ];
          ReadWritePaths = [
            "/.snapshots"
            "/persist/minecraft-backup"
            "/run/minecraft-backup"
          ];
          NoNewPrivileges = true;
          ProtectClock = true;
          ProtectKernelTunables = true;
          ProtectKernelModules = true;
          ProtectKernelLogs = true;
          ProtectControlGroups = true;
          LockPersonality = true;
          RestrictRealtime = true;
          RestrictSUIDSGID = true;

          # Host loopback is the MSMP endpoint; a private network would isolate it.
          PrivateNetwork = false;
          IPAddressDeny = "any";
          IPAddressAllow = "localhost";
          RestrictAddressFamilies = [
            "AF_UNIX"
            "AF_INET"
            "AF_INET6"
          ];
          # Keep Btrfs ioctl privileges until physical acceptance proves reductions.
        };
      };
    })
  ];
}
