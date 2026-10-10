{
  config,
  pkgs,
  username,
}:

let
  server = config.services.minecraft-servers.servers.survival;
  properties = server.serverProperties;
  inherit (server.symlinks) mods;

  pregenConfig = config.specialisation.minecraft-pregen.configuration;
  pregenServer = pregenConfig.services.minecraft-servers.servers.survival;
  pregenProperties = pregenServer.serverProperties;
  pregenMods = pregenServer.symlinks.mods;
  pregenService = pregenConfig.systemd.services.minecraft-server-survival;

  service = config.systemd.services.minecraft-server-survival;
  backupService = config.systemd.services.minecraft-backup;
  backupTimer = config.systemd.timers.minecraft-backup;
  timerStampFiles = builtins.filter (
    file: file.filePath == "/var/lib/systemd/timers/stamp-minecraft-backup.timer"
  ) config.environment.persistence."/persist".files;
  slice = config.systemd.slices.minecraft.sliceConfig;
  minecraftFs = config.fileSystems."/srv/minecraft";

  managementClients = builtins.filter (
    package: (package.name or "") == "minecraft-msmp"
  ) config.environment.systemPackages;
  managementClient = builtins.head managementClients;
  backupClients = builtins.filter (
    package: (package.name or "") == "minecraft-backup"
  ) config.environment.systemPackages;
  backupClient = builtins.head backupClients;

  msmpSource = ../../../hosts/desktop/minecraft-msmp.py;
  msmpTests = ./test_msmp.py;
  backupSource = ../../../hosts/desktop/minecraft-backup.py;
  backupTests = ./test_backup.py;
  prerequisiteSource = ../../../hosts/desktop/minecraft-prerequisites.py;
  prerequisiteTests = ./test_prerequisites.py;

  msmpTestPython = pkgs.python3.withPackages (pythonPackages: [
    pythonPackages.websockets
  ]);
in
assert config.services.minecraft-servers.enable;
assert config.services.minecraft-servers.eula;
assert !config.services.minecraft-servers.openFirewall;
assert config.services.minecraft-servers.dataDir == "/srv/minecraft";
assert
  config.services.minecraft-servers.environmentFile == "/persist/secrets/minecraft-management.env";

assert config.system.preSwitchChecks ? minecraft;
assert pkgs.lib.hasInfix "minecraft-prerequisites" config.system.preSwitchChecks.minecraft;

assert server.files."config/spark/config.json".value.backgroundProfiler == false;
assert
  builtins.attrNames (
    pkgs.lib.filterAttrs (_: entry: entry.enable) config.services.minecraft-servers.servers
  ) == [ "survival" ];
assert server.enable;
assert server.autoStart;
assert server.restart == "always";
assert server.openFirewall;
assert server.package.name == "minecraft-server-26.3-fabric-0.19.5";
assert server.jvmOpts == "-Xms1G -Xmx6G";
assert server.symlinks ? mods;
assert pkgs.lib.hasInfix "MINECRAFT_MANAGEMENT_SECRET" server.extraStartPre;
assert pkgs.lib.hasInfix "^[A-Za-z0-9]{40}$" server.extraStartPre;

assert pkgs.lib.hasInfix "/bin/chmod 0600 server.properties" server.extraStartPre;
assert server.whitelist == { };
assert server.operators == { };
assert
  server.files."config/servercore/optimizations.yml".value == {
    reduce-sync-loads = false;
    cache-ticking-chunks = false;
    optimize-command-blocks = false;
    fast-biome-lookups = false;
    cancel-duplicate-fluid-ticks = false;
  };
assert pregenServer.files == server.files;
assert pregenServer.extraStartPre == server.extraStartPre;

assert properties."server-ip" == "";
assert properties."server-port" == 25565;
assert properties."max-players" == 10;
assert properties."online-mode";
assert properties."white-list";
assert properties."enforce-whitelist";
assert properties."view-distance" == 12;
assert properties."simulation-distance" == 8;
assert properties."pause-when-empty-seconds" == 60;

assert properties."management-server-enabled";
assert properties."management-server-host" == "127.0.0.1";
assert properties."management-server-port" == 25585;
assert properties."management-server-secret" == "@MINECRAFT_MANAGEMENT_SECRET@";
assert !properties."management-server-tls-enabled";
assert properties."management-server-allowed-origins" == "";
assert properties."status-heartbeat-interval" == 0;

assert !properties."enable-rcon";
assert properties."use-native-transport";

assert pregenServer.enable;
assert pregenServer.package.name == server.package.name;
assert pregenServer.jvmOpts == server.jvmOpts;
assert pregenServer.symlinks ? mods;
assert pregenMods != mods;
assert pregenProperties."pause-when-empty-seconds" == -1;

assert pregenProperties."management-server-enabled";
assert pregenProperties."management-server-host" == properties."management-server-host";
assert pregenProperties."management-server-port" == properties."management-server-port";
assert pregenProperties."management-server-secret" == properties."management-server-secret";
assert
  pregenProperties."management-server-tls-enabled" == properties."management-server-tls-enabled";
assert
  pregenProperties."management-server-allowed-origins"
  == properties."management-server-allowed-origins";
assert pregenProperties."status-heartbeat-interval" == properties."status-heartbeat-interval";

assert service.serviceConfig.Slice == "minecraft.slice";
assert service.serviceConfig.Nice == 5;
assert service.serviceConfig.MemoryHigh == "8G";
assert service.serviceConfig.MemoryMax == "10G";
assert service.serviceConfig.EnvironmentFile == "/persist/secrets/minecraft-management.env";
assert pregenService.serviceConfig.EnvironmentFile == service.serviceConfig.EnvironmentFile;

assert builtins.elem "srv-minecraft.mount" service.requires;
assert builtins.elem "srv-minecraft.mount" service.after;
assert service.unitConfig.ConditionPathIsMountPoint == "/srv/minecraft";

assert slice.CPUWeight == 50;
assert slice.IOWeight == 50;

assert backupService.serviceConfig.Type == "oneshot";
assert backupService.serviceConfig.TimeoutStartSec == "20min";
assert backupService.serviceConfig.Slice == "minecraft.slice";
assert backupService.serviceConfig.Nice == 10;
assert backupService.serviceConfig.CPUWeight == 25;
assert backupService.serviceConfig.IOWeight == 25;
assert backupService.serviceConfig.UMask == "0077";
assert backupService.serviceConfig.User == "root";
assert backupService.serviceConfig.Group == "root";
assert backupService.serviceConfig.ProtectSystem == "strict";
assert backupService.serviceConfig.ProtectHome;
assert backupService.serviceConfig.PrivateTmp;
assert backupService.serviceConfig.ReadOnlyPaths == [ "/srv/minecraft" ];
assert
  backupService.serviceConfig.ReadWritePaths == [
    "/.snapshots"
    "/persist/minecraft-backup"
    "/run/minecraft-backup"
  ];
assert backupService.serviceConfig.NoNewPrivileges;
assert backupService.serviceConfig.ProtectClock;
assert backupService.serviceConfig.ProtectKernelTunables;
assert backupService.serviceConfig.ProtectKernelModules;
assert backupService.serviceConfig.ProtectKernelLogs;
assert backupService.serviceConfig.ProtectControlGroups;
assert backupService.serviceConfig.LockPersonality;
assert backupService.serviceConfig.RestrictRealtime;
assert backupService.serviceConfig.RestrictSUIDSGID;
assert !backupService.serviceConfig.PrivateNetwork;
assert backupService.serviceConfig.IPAddressDeny == "any";
assert backupService.serviceConfig.IPAddressAllow == "localhost";
assert
  backupService.serviceConfig.RestrictAddressFamilies == [
    "AF_UNIX"
    "AF_INET"
    "AF_INET6"
  ];
assert !(backupService.serviceConfig ? RuntimeDirectory);
assert !(backupService.serviceConfig ? CapabilityBoundingSet);
assert !(backupService.serviceConfig ? SystemCallFilter);
assert builtins.elem "d /run/minecraft-backup 0700 root root -" config.systemd.tmpfiles.rules;

assert backupTimer.enable;
assert backupTimer.wantedBy == [ "timers.target" ];
assert backupTimer.timerConfig.OnCalendar == "*-*-* 00,06,12,18:00:00 UTC";
assert backupTimer.timerConfig.Persistent;
assert backupTimer.timerConfig.AccuracySec == "5min";
assert backupTimer.timerConfig.Unit == "minecraft-backup.service";
assert !pregenConfig.systemd.timers.minecraft-backup.enable;
assert pregenConfig.systemd.timers.minecraft-backup.wantedBy == [ ];
assert !pregenConfig.systemd.units."minecraft-backup.timer".enable;
assert pregenConfig.systemd.services.minecraft-backup.serviceConfig == backupService.serviceConfig;
assert builtins.elem "minecraft-backup-timer-stamp-seed.service"
  config.systemd.services.${pkgs.lib.removeSuffix ".service" (builtins.head backupTimer.requires)}.requires;
assert builtins.elem "minecraft-backup-timer-stamp-seed.service"
  config.systemd.services.${pkgs.lib.removeSuffix ".service" (builtins.head backupTimer.requires)}.after;
assert
  config.systemd.services.minecraft-backup-timer-stamp-seed.unitConfig.DefaultDependencies == false;
assert
  config.systemd.services.minecraft-backup-timer-stamp-seed.unitConfig.RequiresMountsFor
  == [ "/persist" ];
assert config.systemd.services.minecraft-backup-timer-stamp-seed.serviceConfig.Type == "oneshot";
assert builtins.length timerStampFiles == 1;
assert (builtins.head timerStampFiles).parentDirectory.mode == "0755";
assert builtins.length backupTimer.requires == 1;
assert backupTimer.after == backupTimer.requires;
assert builtins.hasAttr (pkgs.lib.removeSuffix ".service" (
  builtins.head backupTimer.requires
)) config.systemd.services;

assert builtins.elem "/srv/minecraft" backupService.unitConfig.RequiresMountsFor;
assert builtins.elem "/.snapshots" backupService.unitConfig.RequiresMountsFor;
assert builtins.elem "/persist" backupService.unitConfig.RequiresMountsFor;
assert builtins.elem "d /persist/minecraft-backup 0700 root root -" config.systemd.tmpfiles.rules;
assert
  backupService.unitConfig.ConditionPathIsMountPoint == [
    "/srv/minecraft"
    "/.snapshots"
  ];

assert pkgs.lib.hasInfix "minecraft-backup" backupService.serviceConfig.ExecStart;
assert pkgs.lib.hasInfix "minecraft-server-survival.service"
  backupService.serviceConfig.ExecCondition;
assert pkgs.lib.hasInfix "minecraft-backup recover-autosave"
  backupService.serviceConfig.ExecStopPost;

assert minecraftFs.fsType == "btrfs";
assert builtins.elem "subvol=@minecraft" minecraftFs.options;

assert builtins.elem 25565 config.networking.firewall.allowedTCPPorts;
assert !(builtins.elem 25565 config.networking.firewall.allowedUDPPorts);
assert !(builtins.elem 25585 config.networking.firewall.allowedTCPPorts);
assert !(builtins.elem 25585 config.networking.firewall.allowedUDPPorts);

assert builtins.elem "minecraft" config.users.users.${username}.extraGroups;

assert builtins.length managementClients == 1;
assert managementClient.name == "minecraft-msmp";
assert builtins.length backupClients == 1;

pkgs.runCommand "check-minecraft-server-config"
  {
    inherit
      prerequisiteSource
      prerequisiteTests
      backupSource
      backupTests
      backupClient
      managementClient
      mods
      msmpSource
      msmpTests
      pregenMods
      ;

    nativeBuildInputs = [
      msmpTestPython
      pkgs.coreutils
      pkgs.diffutils
      pkgs.jq
      pkgs.unzip
    ];
  }
  ''
        set -eu

        MINECRAFT_PREREQUISITES_SOURCE="$prerequisiteSource" python3 "$prerequisiteTests"

        MINECRAFT_MSMP_SOURCE="$msmpSource" python3 "$msmpTests"

        MINECRAFT_MSMP_SOURCE="$msmpSource" MINECRAFT_BACKUP_SOURCE="$backupSource" python3 "$backupTests"

        "$backupClient/bin/minecraft-backup" --help | grep -F 'status [--live]|recover-autosave'
        "$backupClient/bin/minecraft-backup" status | jq -e '.managed_snapshot_count == 0'
        if "$backupClient/bin/minecraft-backup" invalid-command >/dev/null 2>&1; then
          echo "minecraft-backup accepted an invalid command" >&2
          exit 1
        fi

        client="$managementClient/bin/minecraft-msmp"
        validSecret="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd"

        if [ ! -x "$client" ]; then
          echo "minecraft-msmp executable is missing" >&2
          exit 1
        fi

        helpOutput="$("$client" --help)"

        case "$helpOutput" in
          *"{validate,discover,call,save-and-wait,watch}"*)
            ;;
          *)
            echo "minecraft-msmp help output is missing expected commands" >&2
            exit 1
            ;;
        esac

        validateOutput="$(
          MINECRAFT_MANAGEMENT_SECRET="$validSecret"             "$client" validate
        )"

        if [ "$validateOutput" != "configuration valid: ws://127.0.0.1:25585" ]; then
          echo "minecraft-msmp default configuration validation differed from expected output" >&2
          exit 1
        fi

        if           MINECRAFT_MANAGEMENT_SECRET="too-short"             "$client" validate >/dev/null 2>&1
        then
          echo "minecraft-msmp accepted a short management secret" >&2
          exit 1
        fi

        if           MINECRAFT_MANAGEMENT_SECRET="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabc!"             "$client" validate >/dev/null 2>&1
        then
          echo "minecraft-msmp accepted a non-alphanumeric management secret" >&2
          exit 1
        fi

        managementEnv="$TMPDIR/minecraft-management.env"

        cat > "$managementEnv" <<'EOF'
    MINECRAFT_MANAGEMENT_SECRET=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd
    EOF

        env           -u MINECRAFT_MANAGEMENT_SECRET           MINECRAFT_MANAGEMENT_ENV_FILE="$managementEnv"           "$client" validate >/dev/null

        cat > "$managementEnv" <<'EOF'
    MINECRAFT_MANAGEMENT_SECRET=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd
    MINECRAFT_MANAGEMENT_SECRET=abcd0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
    EOF

        if           env             -u MINECRAFT_MANAGEMENT_SECRET             MINECRAFT_MANAGEMENT_ENV_FILE="$managementEnv"             "$client" validate >/dev/null 2>&1
        then
          echo "minecraft-msmp accepted duplicate secret assignments" >&2
          exit 1
        fi

        if           MINECRAFT_MANAGEMENT_SECRET="$validSecret"           MINECRAFT_MANAGEMENT_URL="ws://192.0.2.1:25585"             "$client" validate >/dev/null 2>&1
        then
          echo "minecraft-msmp accepted a non-loopback management endpoint" >&2
          exit 1
        fi

        if           MINECRAFT_MANAGEMENT_SECRET="$validSecret"           MINECRAFT_MANAGEMENT_URL="wss://127.0.0.1:25585"             "$client" validate >/dev/null 2>&1
        then
          echo "minecraft-msmp accepted TLS despite the configured plaintext loopback endpoint" >&2
          exit 1
        fi

        normalActual="$TMPDIR/minecraft-mods.txt"
        normalExpected="$TMPDIR/expected-minecraft-mods.txt"
        pregenActual="$TMPDIR/minecraft-pregen-mods.txt"
        pregenExpected="$TMPDIR/expected-minecraft-pregen-mods.txt"

        extract_mods() {
          farm="$1"
          output="$2"

          for jar in "$farm"/*.jar; do
            unzip -p "$jar" fabric.mod.json |
              jq -r '.id + " " + .version'
          done | sort > "$output"
        }

        extract_mods "$mods" "$normalActual"
        extract_mods "$pregenMods" "$pregenActual"

        cat > "$normalExpected" <<'EOF'
    fabric-api 0.162.0+26.3
    ferritecore 9.0.0
    lithium 0.26.2+mc26.3
    servercore 1.5.20+26.3
    spark 1.10.187
    EOF

        cat > "$pregenExpected" <<'EOF'
    chunky 1.5.3
    fabric-api 0.162.0+26.3
    ferritecore 9.0.0
    lithium 0.26.2+mc26.3
    servercore 1.5.20+26.3
    spark 1.10.187
    EOF

        if ! diff -u "$normalExpected" "$normalActual"; then
          echo "Minecraft server normal mod set differs from the pinned baseline" >&2
          exit 1
        fi

        if ! diff -u "$pregenExpected" "$pregenActual"; then
          echo "Minecraft server pregen mod set differs from the pinned baseline" >&2
          exit 1
        fi

        echo "Minecraft server configuration invariants passed"
        touch "$out"
  ''
