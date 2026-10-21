{
  pkgs,
  pkgsUnstable,
  config,
  username,
}:

let
  homePolicy = config.home-manager.users.${username}.home.persistence."/persist";
  systemPolicy = config.environment.persistence."/persist";
  homeDirectories = map (entry: entry.directory) homePolicy.directories;
  systemDirectories = map (entry: entry.directory) systemPolicy.directories;
  gpuPolicy = builtins.readFile config.hardware.lactPolicy.source;
  seed = config.systemd.services.gpu-lact-config-seed;
  systemFiles = map (entry: entry.file) systemPolicy.files;
  topologyValid =
    !(config.fileSystems ? "/home")
    && !(config.fileSystems ? "/var")
    && config.fileSystems."/persist".neededForBoot
    && config.boot.ephemeralBtrfsRoot.enable
    && !config.specialisation.persistent-root.configuration.boot.ephemeralBtrfsRoot.enable;
  # Force toplevel evaluation (including NixOS assertions) for both boot
  # policies. Discard the string context so CI does not build either closure.
  evaluation = builtins.unsafeDiscardStringContext (
    builtins.toJSON {
      desktop = config.system.build.toplevel.drvPath;
      persistentRoot = config.specialisation.persistent-root.configuration.system.build.toplevel.drvPath;
      stateVersion = config.system.stateVersion;
    }
  );
in
assert topologyValid;
assert config.hardware.amdgpu.overdrive.enable;
assert config.services.lact.enable;
assert config.services.lact.package == import ../../packages/lact { inherit (pkgsUnstable) lact; };
assert config.hardware.lactPolicy.enable;
assert config.services.lact.settings == { };
assert seed.serviceConfig.Type == "oneshot" && seed.serviceConfig.RemainAfterExit;
assert builtins.elem "lactd.service" seed.before;
assert builtins.elem "lactd.service" seed.requiredBy;
assert builtins.elem "gpu-lact-config-seed.service" config.systemd.services.lactd.requires;
assert builtins.elem config.hardware.lactPolicy.source seed.restartTriggers;
assert builtins.elem config.hardware.lactPolicy.source
  config.systemd.services.lactd.restartTriggers;
assert pkgs.lib.hasInfix "current_profile: Daily\n" gpuPolicy;
assert pkgs.lib.hasInfix "auto_switch_profiles: false\n" gpuPolicy;
assert pkgs.lib.hasInfix "  Stock:\n" gpuPolicy;
assert pkgs.lib.hasInfix "  Daily:\n" gpuPolicy;
assert pkgs.lib.hasInfix "  Gaming:\n" gpuPolicy;
assert !(builtins.elem "/etc/lact" systemDirectories);
assert config.programs.gamemode.gpuProfile.enable;
assert pkgs.lib.hasSuffix "/bin/gamemode-gpu-profile start"
  config.programs.gamemode.settings.custom.start;
assert pkgs.lib.hasSuffix "/bin/gamemode-gpu-profile end"
  config.programs.gamemode.settings.custom.end;
assert pkgs.lib.all (path: !(builtins.elem path homeDirectories)) [
  ".config"
  ".local"
  ".cache"
];
assert pkgs.lib.all (path: builtins.elem path homeDirectories) [
  "Documents"
  "Development"
  ".codex"
  ".ssh"
  ".config/mozilla/firefox"
  ".local/state/fuzzel"
];
assert
  config.home-manager.users.${username}.programs.fuzzel.settings.main.cache
  == "${config.home-manager.users.${username}.xdg.stateHome}/fuzzel/history";
assert builtins.elem "/var/lib/systemd/random-seed" systemFiles;
assert config.services.journald.storage == "volatile";
pkgs.runCommand "check-desktop-evaluation" { inherit evaluation; } ''
  printf '%s\n' "$evaluation" > "$out"
''
