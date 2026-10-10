{
  pkgs,
  config,
  homeCutover,
}:

let
  homePolicy = config.home-manager.users.p2949.home.persistence."/persist";
  systemPolicy = config.environment.persistence."/persist";
  homeDirectories = map (entry: entry.directory) homePolicy.directories;
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
      homeMigration = homeCutover.system.build.toplevel.drvPath;
      stateVersion = config.system.stateVersion;
    }
  );
in
assert topologyValid;
assert homeCutover.workstation.granularMigration.keepLegacyVar;
assert !(homeCutover.fileSystems ? "/home");
assert homeCutover.fileSystems."/var".neededForBoot;
assert pkgs.lib.elem "subvol=@var" homeCutover.fileSystems."/var".options;
assert
  !(builtins.elem "/var/lib/systemd/random-seed" (
    map (entry: entry.file) homeCutover.environment.persistence."/persist".files
  ));
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
  config.home-manager.users.p2949.programs.fuzzel.settings.main.cache
  == "${config.home-manager.users.p2949.xdg.stateHome}/fuzzel/history";
assert
  homeCutover.home-manager.users.p2949.programs.fuzzel.settings.main.cache
  == "${homeCutover.home-manager.users.p2949.xdg.stateHome}/fuzzel/history";
assert builtins.elem ".local/state/fuzzel" (
  map (
    entry: entry.directory
  ) homeCutover.home-manager.users.p2949.home.persistence."/persist".directories
);
assert builtins.elem "/var/lib/systemd/random-seed" systemFiles;
assert config.services.journald.storage == "volatile";
pkgs.runCommand "check-desktop-evaluation" { inherit evaluation; } ''
  printf '%s\n' "$evaluation" > "$out"
''
