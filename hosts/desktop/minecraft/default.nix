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
  mods = import ./mods.nix { inherit pkgs; };
  baseModDrvsByName = builtins.removeAttrs mods [ "chunky" ];
  baseModDrvs = builtins.attrValues baseModDrvsByName;
  inherit (mods) chunky;

  baseMods = pkgs.linkFarmFromDrvs "minecraft-survival-mods" baseModDrvs;

  # Chunky generation must run without Distant Horizons loaded. DH observes
  # generated chunks even with its generator disabled, and its LOD backlog can
  # exhaust the pregeneration JVM heap under sustained Chunky throughput.
  pregenMods = pkgs.linkFarmFromDrvs "minecraft-survival-pregen-mods" (
    builtins.attrValues (builtins.removeAttrs baseModDrvsByName [ "distant-horizons" ]) ++ [ chunky ]
  );

  minecraftManagementPython = pkgs.python3.withPackages (pythonPackages: [
    pythonPackages.websockets
  ]);

  minecraftManagementClient = pkgs.writeShellApplication {
    name = "minecraft-msmp";
    text = ''
      exec ${minecraftManagementPython}/bin/python3 ${../minecraft-msmp.py} "$@"
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
      exec ${pkgs.python3}/bin/python3 ${../minecraft-prerequisites.py}
    '';
  };

  minecraftBackupRunner = pkgs.writeShellApplication {
    name = "minecraft-backup";

    runtimeInputs = [
      pkgs.btrfs-progs
    ];

    text = ''
      export MINECRAFT_MSMP_SOURCE=${../minecraft-msmp.py}
      exec ${minecraftManagementPython}/bin/python3 ${../minecraft-backup.py} "$@"
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
            "-Xmx8G"
            "-XX:+ExitOnOutOfMemoryError"
            "-XX:+UseG1GC"
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

          files."config/c2me.toml".value = {
            version = 3;
            globalExecutorParallelism = 4;
          };

          files."config/spark/config.json".value.backgroundProfiler = false;

          # Verified against the generated schema and commands of DH 3.3.4.
          # CHUNKS_ONLY avoids the surface pass; only existing chunks supply LODs.
          # MINIMAL_IMPACT on this 12-thread host: ceil(12 * 0.1), ratio 0.5.
          files."config/DistantHorizons.toml".value = {
            _version = 5;
            server = {
              synchronizeOnLoad = true;
              enableRealTimeUpdates = true;
            };
            common.worldGenerator = {
              chunkGeneratorMode = "PRE_EXISTING_ONLY";
              generatorPlan = "CHUNKS_ONLY";
            };
            common.multiThreading = {
              numberOfThreads = 2;
              threadRunTimeRatio = "0.5";
            };
          };

          extraStartPre = ''
            ${pkgs.python3}/bin/python3 ${../minecraft-dh-identity.py} apply
            ${pkgs.coreutils}/bin/chmod 0600 server.properties
            if [[ ! "''${MINECRAFT_MANAGEMENT_SECRET:-}" =~ ^[A-Za-z0-9]{40}$ ]]; then
              echo "Minecraft management secret must be exactly 40 alphanumeric characters" >&2
              exit 1
            fi
          '';
          extraStopPre = ''
            ${pkgs.python3}/bin/python3 ${../minecraft-dh-identity.py} capture
          '';

          symlinks.mods = baseMods;

          serverProperties = {
            server-ip = "";
            server-port = 25565;
            max-players = 10;

            spawn-protection = 0;

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

        systemd.services.minecraft-server-survival.serviceConfig = {
          MemoryHigh = lib.mkForce "14G";
          MemoryMax = lib.mkForce "16G";
        };

        services.minecraft-servers.servers.survival = {
          symlinks.mods = lib.mkForce pregenMods;

          jvmOpts = lib.mkForce [
            "-Xms1G"
            "-Xmx10G"
            "-XX:+ExitOnOutOfMemoryError"
            "-XX:+UseG1GC"
            "-Xlog:gc*,safepoint:file=logs/gc-pregen.log:time,uptime,level,tags:filecount=5,filesize=20M"
          ];

          serverProperties."pause-when-empty-seconds" = lib.mkForce (-1);

          files."config/chunky/config.json".value = {
            version = 2;
            language = "en";
            continueOnRestart = true;
            forceLoadExistingChunks = false;
            silent = false;
            updateInterval = 1;
          };

          files."config/DistantHorizons.toml".value.common.worldGenerator.generatorPlan =
            lib.mkForce "DISABLED";
        };
      };

      specialisation.minecraft-dh-lod-backfill.configuration = {
        systemd.timers.minecraft-backup = {
          enable = lib.mkForce false;
          wantedBy = lib.mkForce [ ];
        };
        services.minecraft-servers.servers.survival = {
          serverProperties."pause-when-empty-seconds" = lib.mkForce (-1);
          # DH LOD backfill must consume only vanilla chunks that already exist.
          # INTERNAL_SERVER was live-proven to allocate additional boundary chunks.
          files."config/DistantHorizons.toml".value.common.worldGenerator = {
            chunkGeneratorMode = lib.mkForce "PRE_EXISTING_ONLY";
            generatorPlan = lib.mkForce "CHUNKS_ONLY";
          };
        };
      };

      system.preSwitchChecks.minecraft = ''${lib.getExe minecraftPrerequisiteCheck} "$@"'';

      # nix-minecraft removes its previous managed files before applying templates.
      # Capture the generated ID first so restarts keep the same DH cache identity.
      systemd.services.minecraft-server-survival.preStart = lib.mkBefore ''
        ${pkgs.python3}/bin/python3 ${../minecraft-dh-identity.py} capture
      '';

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

          MemoryHigh = "10G";
          MemoryMax = "12G";
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
