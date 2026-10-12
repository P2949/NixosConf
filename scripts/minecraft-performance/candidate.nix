{
  candidateUri,
  withC2ME ? false,
}:
let
  flake = builtins.getFlake candidateUri;
  system = flake.nixosConfigurations.desktop;
  cfg = system.config;
  inherit (system) pkgs;
  server = cfg.services.minecraft-servers.servers.survival;
  pregen =
    cfg.specialisation.minecraft-pregen.configuration.services.minecraft-servers.servers.survival;
  unit = cfg.systemd.services.minecraft-server-survival.serviceConfig;
  qualificationMods =
    directory:
    if withC2ME then
      directory
    else
      pkgs.runCommand "minecraft-control-without-c2me" { } ''
        mkdir "$out"
        for mod in ${directory}/*.jar; do
          case "$(basename "$mod")" in
            c2me-*) ;;
            *) ln -s "$mod" "$out/" ;;
          esac
        done
      '';
  dhPregen =
    cfg.specialisation.minecraft-dh-pregen.configuration.services.minecraft-servers.servers.survival;
  memoryBytes =
    value:
    if builtins.isInt value then
      value
    else
      let
        parts = builtins.match "([0-9]+)([KMGT])" value;
        factors = {
          K = 1024;
          M = 1048576;
          G = 1073741824;
          T = 1099511627776;
        };
      in
      if parts == null then
        throw "Unsupported qualification memory limit"
      else
        pkgs.lib.toInt (builtins.elemAt parts 0) * factors.${builtins.elemAt parts 1};
  policyFiles = builtins.mapAttrs (
    name: value:
    if builtins.isString value || builtins.isPath value then
      value
    else
      (
        if value ? format && value.format != null then
          value.format
        else if pkgs.lib.hasSuffix ".toml" name then
          pkgs.formats.toml { }
        else if pkgs.lib.hasSuffix ".json" name then
          pkgs.formats.json { }
        else
          pkgs.formats.yaml { }
      ).generate
        name
        value.value
  ) server.files;
  queueAgent =
    pkgs.runCommand "minecraft-qualification-queue-agent"
      {
        nativeBuildInputs = [ pkgs.openjdk25 ];
        agentSource = flake.outPath + "/scripts/minecraft-performance/probe/DhQueueAgent.java";
        attachSource = flake.outPath + "/scripts/minecraft-performance/probe/QueueAttach.java";
      }
      ''
        mkdir -p classes "$out"
        javac -d classes "$agentSource" "$attachSource"
        printf 'Manifest-Version: 1.0\nAgent-Class: local.minecraft.performance.DhQueueAgent\n\n' > agent.manifest
        jar --create --date=2026-01-01T00:00:00Z --file "$out/queue-agent.jar" \
          --manifest agent.manifest -C classes .
      '';
in
pkgs.writeText "minecraft-candidate-nix.json" (
  builtins.toJSON {
    schema = 1;
    qualification_tools_path = pkgs.lib.makeBinPath [
      pkgs.coreutils
      pkgs.btrfs-progs
      pkgs.systemd
      pkgs.git
      pkgs.procps
    ];
    git_sha = flake.rev;
    system_closure = cfg.system.build.toplevel;
    minecraft_package = server.package;
    minecraft_package_name = server.package.name;
    java_home = pkgs.openjdk25_headless;
    diagnostic_java_home = pkgs.openjdk25;
    queue_agent_path = "${queueAgent}/queue-agent.jar";
    mods_directory = qualificationMods server.symlinks.mods;
    pregen_mods_directory = qualificationMods pregen.symlinks.mods;
    pregen_dh_policy =
      (pkgs.formats.toml { }).generate "config-DistantHorizons-pregen.toml"
        pregen.files."config/DistantHorizons.toml".value;
    pregen_pause_seconds = pregen.serverProperties.pause-when-empty-seconds;
    jvm_flags = pkgs.lib.splitString " " server.jvmOpts;
    policy_files =
      if withC2ME then policyFiles else builtins.removeAttrs policyFiles [ "config/c2me.toml" ];
    dh_pregen_mods_directory = qualificationMods dhPregen.symlinks.mods;
    dh_pregen_dh_policy =
      (pkgs.formats.toml { }).generate "config-DistantHorizons-dh-pregen.toml"
        dhPregen.files."config/DistantHorizons.toml".value;
    dh_pregen_pause_seconds = dhPregen.serverProperties.pause-when-empty-seconds;
    mode_backup_timers = {
      normal = cfg.systemd.timers.minecraft-backup.enable;
      chunky = cfg.specialisation.minecraft-pregen.configuration.systemd.timers.minecraft-backup.enable;
      dh_pregen =
        cfg.specialisation.minecraft-dh-pregen.configuration.systemd.timers.minecraft-backup.enable;
    };
    server_properties = server.serverProperties;
    service = {
      MemoryHighBytes = memoryBytes unit.MemoryHigh;
      MemoryMaxBytes = memoryBytes unit.MemoryMax;
      inherit (unit)
        Nice
        MemoryHigh
        MemoryMax
        Slice
        ;
      inherit (cfg.systemd.slices.minecraft.sliceConfig) CPUWeight IOWeight;
    };
  }
)
