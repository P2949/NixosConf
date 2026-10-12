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
  c2me = import (flake.outPath + "/scripts/minecraft-performance/c2me.nix") { inherit pkgs; };
  qualificationMods =
    directory:
    if withC2ME then
      pkgs.runCommand "minecraft-c2me-qualification-mods" { } ''
        mkdir "$out"
        cp -s ${directory}/*.jar "$out/"
        ln -s ${c2me} "$out/c2me-fabric-mc26.3-0.4.2-alpha.0.90.jar"
      ''
    else
      directory;
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
      policyFiles
      // pkgs.lib.optionalAttrs withC2ME {
        # Pinned ConfigSystem requires schema version 3; ModuleEntryPoint reads
        # globalExecutorParallelism at the root and logs its effective value.
        "config/c2me.toml" = (pkgs.formats.toml { }).generate "c2me-qualification.toml" {
          version = 3;
          globalExecutorParallelism = 4;
        };
      };
    server_properties = server.serverProperties;
    service = {
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
