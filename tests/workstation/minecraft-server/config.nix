{
  config,
  pkgs,
  username,
}:

let
  server = config.services.minecraft-servers.servers.survival;
  properties = server.serverProperties;
  inherit (server.symlinks) mods;

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

  minecraftTools = pkgs.callPackage ../../../packages/minecraft-tools { };
  msmpTestPython = pkgs.python3.withPackages (pythonPackages: [ pythonPackages.websockets ]);

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
assert server.jvmOpts == "-Xms1G -Xmx8G -XX:+ExitOnOutOfMemoryError -XX:+UseG1GC";
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
assert
  server.files."config/c2me.toml".value == {
    version = 3;
    globalExecutorParallelism = 4;
  };
assert server.files."config/chunky/config.json".value.continueOnRestart;
assert !(config.specialisation ? minecraft-pregen);
assert !(config.specialisation ? minecraft-dh-lod-backfill);

assert properties."server-ip" == "";
assert properties."server-port" == 25565;
assert properties."max-players" == 10;
assert properties."online-mode";
assert properties."white-list";
assert properties."enforce-whitelist";
assert properties."view-distance" == 12;
assert properties."simulation-distance" == 8;
assert properties."pause-when-empty-seconds" == -1;

assert properties."management-server-enabled";
assert properties."management-server-host" == "127.0.0.1";
assert properties."management-server-port" == 25585;
assert properties."management-server-secret" == "@MINECRAFT_MANAGEMENT_SECRET@";
assert !properties."management-server-tls-enabled";
assert properties."management-server-allowed-origins" == "";
assert properties."status-heartbeat-interval" == 0;

assert !properties."enable-rcon";
assert properties."use-native-transport";

assert service.serviceConfig.Slice == "minecraft.slice";
assert service.serviceConfig.Nice == 5;
assert service.serviceConfig.MemoryHigh == "10G";
assert service.serviceConfig.MemoryMax == "12G";
assert service.serviceConfig.EnvironmentFile == "/persist/secrets/minecraft-management.env";

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
assert backupClient.name == "minecraft-backup";

pkgs.runCommand "check-minecraft-server-config"
  {
    inherit mods;

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
        export PYTHONPATH="${minecraftTools}/${pkgs.python3.sitePackages}"

        python3 -c 'from pathlib import Path; import sys; from minecraft_tools.config import load_config; policy = load_config(Path(sys.argv[1])); assert str(policy.source) == "/srv/minecraft"; assert policy.management_port == 25585; assert policy.source_fs_root == "/@minecraft"; assert policy.snapshot_fs_root == "/@snapshots"' ${
          config.environment.etc."minecraft-tools.json".source
        }
        normalActual="$TMPDIR/minecraft-mods.txt"
        normalExpected="$TMPDIR/expected-minecraft-mods.txt"

        extract_mods() {
          farm="$1"
          output="$2"

          for jar in "$farm"/*.jar; do
            unzip -p "$jar" fabric.mod.json |
              jq -r '.id + " " + .version'
          done | sort > "$output"
        }

        extract_mods "$mods" "$normalActual"

        cat > "$normalExpected" <<'EOF'
    c2me 0.4.2-alpha.0.90+26.3
    chunky 1.5.3
    fabric-api 0.162.0+26.3
    ferritecore 9.0.0
    krypton 0.3.2
    lithium 0.26.2+mc26.3
    mr_chunky_offline 1-v1.1.0
    servercore 1.5.20+26.3
    spark 1.10.187
    EOF

        if ! diff -u "$normalExpected" "$normalActual"; then
          echo "Minecraft server normal mod set differs from the pinned baseline" >&2
          exit 1
        fi

        python3 - "$mods" ${../../../hosts/desktop/minecraft/chunky-offline} <<'PYTEST'
    import json
    import re
    import sys
    import zipfile
    from pathlib import Path

    jars = [zipfile.ZipFile(p) for p in Path(sys.argv[1]).glob("*.jar")]
    pack = next(j for j in jars if json.loads(j.read("fabric.mod.json"))["id"] == "mr_chunky_offline")
    prefix = "data/chunky_offline/function/"
    owned = Path(sys.argv[2])
    for source in owned.glob("*.mcfunction"):
        assert pack.read(prefix + source.name) == source.read_bytes(), source.name
    functions = {Path(n).name: pack.read(n).decode() for n in pack.namelist() if n.startswith(prefix) and n.endswith(".mcfunction")}
    assert set(functions) == {p.name for p in owned.glob("*.mcfunction")}
    policy = functions["policy.mcfunction"]
    for world, radius, threshold in [("overworld", 10000, 7500), ("the_nether", 1250, 938), ("the_end", 5000, 3750)]:
        assert f'world:"minecraft:{world}",radius:{radius},threshold:{threshold}' in policy
    load = functions["load.mcfunction"]
    assert 'unless data storage chunky_offline:tracking overworld' in load
    assert 'overworld set value {enabled:1b,hasTask:1b,centerX:0,centerZ:0' in load
    for key in ["nether", "end"]:
        assert f'unless data storage chunky_offline:tracking {key}' in load
        assert f'{key} set value {{enabled:0b,hasTask:0b' in load
    assert 'matches 200..' in functions["online.mcfunction"]
    assert 'chunky pause' in functions["online.mcfunction"]
    assert 'chunky continue' in functions["offline.mcfunction"]
    assert 'execute if entity @a run return 0' in functions["replace.mcfunction"]
    assert 'chunky cancel $(world)' in functions["replace.mcfunction"]
    assert 'chunky start $(world) square $(lastActivityX) $(lastActivityZ) $(radius)' in functions["replace.mcfunction"]
    assert not re.search(r'chunky cancel["}]', "\n".join(functions.values()))
    PYTEST

        echo "Minecraft server configuration invariants passed"
        touch "$out"
  ''
