{ config, lib, pkgs, utils, ... }:
let
  cfg = config.workstation.ephemeralHomeDirectories;
  home = config.users.users.${cfg.user}.home;
  policy = config.home-manager.users.${cfg.user}.home.persistence."/persist";
  persistedParents = map (entry: entry.directory) policy.directories;
  entries = lib.concatMap (entry: map (child: {
    inherit (entry) parent;
    relative = "${entry.parent}/${child}";
  }) entry.children) cfg.paths;
  source = entry: "${home}/.cache/ephemeral-app-state/${entry.relative}";
  target = entry: "${home}/${entry.relative}";
  safeRelative = path:
    !(lib.hasPrefix "/" path) && lib.all (part: part != "" && part != "." && part != "..") (lib.splitString "/" path);
in
{
  options.workstation.ephemeralHomeDirectories = {
    enable = lib.mkEnableOption "root-local cache children of persistent application profiles";
    user = lib.mkOption { type = lib.types.str; };
    paths = lib.mkOption {
      type = lib.types.listOf (lib.types.submodule {
        options = {
          parent = lib.mkOption { type = lib.types.str; };
          children = lib.mkOption { type = lib.types.listOf lib.types.str; };
        };
      });
      default = [ ];
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = lib.all (entry: safeRelative entry.relative && lib.elem entry.parent persistedParents) entries;
        message = "Ephemeral application children must be safe relative paths under an explicitly persisted parent.";
      }
      {
        assertion = !(config.fileSystems ? "/home")
          && lib.all (entry: !(lib.hasPrefix ".cache" entry.directory)) policy.directories;
        message = "Ephemeral application backing directories must live on the reset root, never on persistent home/cache mounts.";
      }
      {
        assertion = lib.all (entry: lib.all (other: entry == other || !(lib.hasPrefix "${entry.relative}/" other.relative)) entries) entries;
        message = "Ephemeral application directory declarations must not nest within each other.";
      }
    ];

    # Activation runs before systemd starts the real-root mount units. Create
    # empty mountpoint scaffolding in the backing profile as well, so a fresh
    # install works without having launched any application first.
    system.activationScripts.ephemeralApplicationDirectories = {
      deps = [ "createPersistentStorageDirs" ];
      text = lib.concatMapStringsSep "\n" (entry: ''
        ${pkgs.coreutils}/bin/install -d -m 0700 -o ${lib.escapeShellArg cfg.user} -g ${lib.escapeShellArg config.users.users.${cfg.user}.group} ${lib.escapeShellArg (source entry)}
        ${pkgs.coreutils}/bin/mkdir -p ${lib.escapeShellArg ("/persist" + target entry)}
      '') entries;
    };

    systemd.mounts = map (entry: {
      what = source entry;
      where = target entry;
      type = "none";
      options = "bind,x-gvfs-hide";
      wantedBy = [ "local-fs.target" ];
      before = [ "local-fs.target" ];
      requires = [ "${utils.escapeSystemdPath "${home}/${entry.parent}"}.mount" ];
      after = [ "${utils.escapeSystemdPath "${home}/${entry.parent}"}.mount" ];
    }) entries;
  };
}
