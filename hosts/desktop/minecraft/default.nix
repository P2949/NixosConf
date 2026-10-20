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
  serverMods = pkgs.linkFarmFromDrvs "minecraft-survival-mods" (builtins.attrValues mods);

  minecraftToolPolicy = {
    schemaVersion = 1;
    source = config.services.minecraft-servers.dataDir;
    snapshotMount = "/.snapshots";
    snapshotRoot = "/.snapshots/minecraft";
    stateDirectory = "/persist/minecraft-backup";
    runtimeDirectory = "/run/minecraft-backup";
    management = {
      host = config.services.minecraft-servers.servers.survival.serverProperties."management-server-host";
      port = config.services.minecraft-servers.servers.survival.serverProperties."management-server-port";
      environmentFile = config.services.minecraft-servers.environmentFile;
    };
    retention.snapshots = 14;
    btrfs = {
      sourceRoot = "/${
        lib.removePrefix "subvol=" (
          lib.findFirst (lib.hasPrefix "subvol=") "" config.fileSystems.${minecraftToolPolicy.source}.options
        )
      }";
      snapshotRoot = "/${
        lib.removePrefix "subvol=" (
          lib.findFirst (lib.hasPrefix "subvol=") ""
            config.fileSystems.${minecraftToolPolicy.snapshotMount}.options
        )
      }";
    };
  };
  minecraftToolConfig = pkgs.writeText "minecraft-tools.json" (builtins.toJSON minecraftToolPolicy);
  minecraftTools = pkgs.callPackage ../../../packages/minecraft-tools { };
  minecraftManagementClient = pkgs.writeShellApplication {
    name = "minecraft-msmp";
    text = ''exec ${minecraftTools}/bin/minecraft-msmp --config ${minecraftToolConfig} "$@"'';
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
    text = "exec ${minecraftTools}/bin/minecraft-prerequisites --config ${minecraftToolConfig}";
  };
  minecraftBackupRunner = pkgs.writeShellApplication {
    name = "minecraft-backup";
    text = ''exec ${minecraftTools}/bin/minecraft-backup --config ${minecraftToolConfig} "$@"'';
  };

in
{
  imports = [
    inputs.nix-minecraft.nixosModules.minecraft-servers
  ];

  config = lib.mkMerge [
    {
      environment.etc."minecraft-tools.json".source = minecraftToolConfig;
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

          files."config/chunky/config.json".value = {
            version = 2;
            language = "en";
            continueOnRestart = true;
            forceLoadExistingChunks = false;
            silent = false;
            updateInterval = 1;
          };

          extraStartPre = ''
            ${pkgs.coreutils}/bin/chmod 0600 server.properties
            if [[ ! "''${MINECRAFT_MANAGEMENT_SECRET:-}" =~ ^[A-Za-z0-9]{40}$ ]]; then
              echo "Minecraft management secret must be exactly 40 alphanumeric characters" >&2
              exit 1
            fi
          '';
          symlinks.mods = serverMods;

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

            # Chunky Offline permanently tracks and generates targets while empty.
            pause-when-empty-seconds = -1;

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
