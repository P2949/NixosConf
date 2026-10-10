{
  config,
  lib,
  pkgs,
  utils,
  ...
}:
let
  cfg = config.workstation.ephemeralApplicationState;
  home = config.users.users.${cfg.user}.home;
  policy = config.home-manager.users.${cfg.user}.home.persistence."/persist";
  persistedParents = map (entry: entry.directory) policy.directories;
  entries = lib.concatMap (
    entry:
    map (child: {
      inherit (entry) parent;
      relative = "${entry.parent}/${child}";
    }) entry.children
  ) cfg.paths;
  disposableFiles = lib.concatMap (
    entry:
    map (child: {
      inherit (entry) parent;
      relative = "${entry.parent}/${child}";
    }) entry.children
  ) cfg.files;
  source = entry: "${home}/.cache/ephemeral-app-state/${entry.relative}";
  target = entry: "${home}/${entry.relative}";
  safeRelative =
    path:
    !(lib.hasPrefix "/" path)
    && lib.all (part: part != "" && part != "." && part != "..") (lib.splitString "/" path);
  applicationChildren = lib.types.submodule {
    options = {
      parent = lib.mkOption {
        type = lib.types.str;
        description = "Home-relative application directory explicitly retained by Home Manager persistence.";
      };
      children = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        description = "Disposable paths relative to the persisted parent directory.";
      };
    };
  };

in
{
  options.workstation.ephemeralApplicationState = {
    enable = lib.mkEnableOption "disposable directories and files within persistent application profiles";
    user = lib.mkOption {
      type = lib.types.str;
      description = "User whose Home Manager persistence policy owns the application profiles.";
    };
    paths = lib.mkOption {
      type = lib.types.listOf applicationChildren;
      default = [ ];
      description = "Disposable directories bind-mounted from the reset root into persistent profiles.";
    };
    files = lib.mkOption {
      type = lib.types.listOf applicationChildren;
      default = [ ];
      description = "Disposable files removed at normal boot; retained by the persistent-root specialisation.";
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = lib.all (entry: safeRelative entry.relative && lib.elem entry.parent persistedParents) (
          entries ++ disposableFiles
        );
        message = "Ephemeral application children must be safe relative paths under an explicitly persisted parent.";
      }
      {
        assertion =
          !(config.fileSystems ? "/home")
          && lib.all (entry: !(lib.hasPrefix ".cache" entry.directory)) policy.directories;
        message = "Ephemeral application backing directories must live on the reset root, never on persistent home/cache mounts.";
      }
      {
        assertion = lib.all (
          entry:
          lib.all (other: entry == other || !(lib.hasPrefix "${entry.relative}/" other.relative)) entries
        ) entries;
        message = "Ephemeral application directory declarations must not nest within each other.";
      }
    ];

    # Activation runs before systemd starts the real-root mount units. Create
    # empty mountpoint scaffolding in the backing profile as well, so a fresh
    # install works without having launched any application first.
    system.activationScripts.ephemeralApplicationDirectories = {
      deps = [ "createPersistentStorageDirs" ];
      text = ''
        ${pkgs.coreutils}/bin/install -d -m 0700 -o ${lib.escapeShellArg cfg.user} -g ${
          lib.escapeShellArg config.users.users.${cfg.user}.group
        } ${lib.escapeShellArg "${home}/.cache"} ${lib.escapeShellArg "${home}/.cache/ephemeral-app-state"}
      ''
      + lib.concatMapStringsSep "\n" (entry: ''
        ${pkgs.coreutils}/bin/install -d -m 0700 -o ${lib.escapeShellArg cfg.user} -g ${
          lib.escapeShellArg config.users.users.${cfg.user}.group
        } ${lib.escapeShellArg (source entry)}
          task_backing=${lib.escapeShellArg ("/persist" + target entry)}
          task_parent=${lib.escapeShellArg "/persist${home}/${entry.parent}"}
          task_missing=()
          while [[ "$task_backing" != "$task_parent" ]]; do
            if [[ ! -d "$task_backing" ]]; then task_missing+=("$task_backing"); fi
            task_backing="''${task_backing%/*}"
          done
          for (( task_index=''${#task_missing[@]}-1; task_index>=0; task_index-- )); do
            ${pkgs.coreutils}/bin/install -d -m 0700 -o ${lib.escapeShellArg cfg.user} -g ${
              lib.escapeShellArg config.users.users.${cfg.user}.group
            } "''${task_missing[task_index]}"
          done
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

    # The ! suffix makes removal boot-only, so a live rebuild cannot remove
    # an open SQLite database. Recovery boots retain all root-local state.
    systemd.tmpfiles.rules = lib.mkIf config.boot.ephemeralBtrfsRoot.enable (
      map (entry: "r! ${lib.escapeShellArg (target entry)} - - - -") disposableFiles
    );
  };
}
