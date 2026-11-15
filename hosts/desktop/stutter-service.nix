{
  config,
  lib,
  pkgs,
  username,
  inputs,
  ...
}:

# Production integration of Stutter's bounded always-on service: a monitored-user controller and
# a separate root worker, exactly the product's own units. Opt-in, because the validation runner
# installs transient units with the same names under /run and a unit in /etc would take
# precedence over them; enable this once campaigns that install their own units are finished.
#
# Trust boundary: the root worker may only execute an immutable, root-owned binary. The binary is
# pinned by the SHA-256 of the file and referenced as a Nix store path, so a writable checkout can
# never become root code. State persists through hosts/desktop/persistence.nix.
let
  cfg = config.services.stutterBounded;
  upstream = "${inputs.stutter}/packaging/systemd";
  binary = pkgs.requireFile {
    name = "stutter";
    sha256 = cfg.binarySha256;
    message = ''
      Add the release binary of the pinned Stutter source to the store first:
        nix-store --add-fixed sha256 /path/to/stutter/target/release/stutter   (built with: cargo build --release -p stutter --features wayland-probe)
      and set services.stutterBounded.binarySha256 to the hash of that file (nix hash file --type sha256 --base16).
    '';
  };
  configDir = "/etc/stutter";
  # Immutable and exact: names the pinned binary by store path, so it is only built and registered
  # for a configuration that explicitly enables live launch.
  dispatcher = pkgs.callPackage ../../packages/proton/dispatcher.nix { } {
    stutterBinary = "${binary}";
    studyDir = cfg.research.studyDir;
  };
  render =
    name:
    let
      template = builtins.readFile "${upstream}/${name}";
      withResearch =
        if cfg.research.enable && name == "stutter-autotune-bounded@.service" then
          builtins.replaceStrings
            [ "ProtectHome=read-only" ]
            [
              "ProtectHome=read-only\nReadWritePaths=${builtins.toJSON cfg.research.studyDir}\nEnvironment=RUST_LOG=warn\nEnvironment=STUTTER_JOURNALCTL=${config.systemd.package}/bin/journalctl"
            ]
            template
        else
          template;
    in
    builtins.replaceStrings
      [ "@BINARY@" "@SYSTEMCTL@" "@CONFIG_DIR@" ]
      [ "${binary}" "${config.systemd.package}/bin/systemctl" configDir ]
      withResearch;
  campaignDir = "/var/lib/stutter/autotune-${cfg.user}/research-campaign";
  socketDir = "/run/stutter-autotune-${cfg.user}";
  absoluteSafe =
    path:
    builtins.match "/[A-Za-z0-9_+./-]+" path != null
    && !(lib.hasInfix "//" path)
    && !(lib.hasInfix "/../" "${path}/")
    && !(lib.hasInfix "/./" "${path}/");
  overlaps =
    left: right:
    left == right
    || lib.hasPrefix "${lib.removeSuffix "/" left}/" right
    || lib.hasPrefix "${lib.removeSuffix "/" right}/" left;
in
{
  options.services.stutterBounded = {
    enable = lib.mkEnableOption "the packaged Stutter bounded always-on service (controller plus root worker)";
    binarySha256 = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "SHA-256 (base16) of the release `stutter` binary added to the Nix store.";
    };
    user = lib.mkOption {
      type = lib.types.str;
      default = username;
      description = "The monitored desktop account the controller runs as.";
    };
    research = {
      enable = lib.mkEnableOption "the separately authorized Stutter research control";
      steamappsDir = lib.mkOption {
        type = lib.types.str;
        default = "/home/${cfg.user}/.local/share/Steam/steamapps";
        description = "Canonical Steam library directory used for read-only inventory.";
      };
      protonManifest = lib.mkOption {
        type = lib.types.str;
        default = toString inputs.self.packages.${pkgs.stdenv.hostPlatform.system}.proton-lab.manifest;
        description = "Absolute immutable proton-lab manifest path from this configuration.";
      };
      studyDir = lib.mkOption {
        type = lib.types.str;
        default = "/home/${cfg.user}/Development/StutterProtonStudies";
        description = "Existing private, persistent directory for research evidence.";
      };
      liveLaunch = lib.mkEnableOption "the composed research launch host (off by default; a campaign still needs its own consented intent, lease and safe window)";
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = builtins.match "[0-9a-f]{64}" cfg.binarySha256 != null;
        message = "services.stutterBounded.binarySha256 must be the 64 hex digit SHA-256 of the pinned binary";
      }
      {
        assertion =
          !cfg.research.enable
          || (
            absoluteSafe cfg.research.steamappsDir
            && lib.hasPrefix "/nix/store/" cfg.research.protonManifest
            && absoluteSafe cfg.research.protonManifest
            && lib.hasPrefix "/home/${cfg.user}/Development/" cfg.research.studyDir
            && absoluteSafe cfg.research.studyDir
            && !(overlaps cfg.research.studyDir cfg.research.steamappsDir)
          );
        message = "Stutter research requires absolute, confined study and Steam paths and an immutable Proton manifest";
      }
      {
        assertion =
          !cfg.research.enable
          ||
            builtins.length (
              lib.splitString "ProtectHome=read-only" (
                builtins.readFile "${upstream}/stutter-autotune-bounded@.service"
              )
            ) == 2;
        message = "Stutter research requires the expected controller home sandbox in the pinned unit template";
      }
      {
        assertion = !cfg.research.liveLaunch || cfg.research.enable;
        message = "services.stutterBounded.research.liveLaunch requires services.stutterBounded.research.enable";
      }
    ];

    # The product's own unit templates, rendered with the immutable binary, never reimplemented here.
    systemd.units."stutter-privileged-worker@.service".text =
      render "stutter-privileged-worker@.service";
    systemd.units."stutter-autotune-bounded@.service".text = render "stutter-autotune-bounded@.service";

    # Administrator configuration, the same file `stutter service install` would create.
    environment.etc."stutter/autotune-bounded-${cfg.user}.toml".text = ''
      [autotune]
      worker_only_mutation = true
      manage_privileged_worker = false
      privileged_worker_socket = "/run/stutter-worker-${cfg.user}/worker.sock"
    ''
    + lib.optionalString cfg.research.enable ''
      research_socket_dir = ${builtins.toJSON socketDir}
      research_campaign_dir = ${builtins.toJSON campaignDir}
      research_study_dir = ${builtins.toJSON cfg.research.studyDir}
      research_steamapps_dir = ${builtins.toJSON cfg.research.steamappsDir}
      research_proton_manifest = ${builtins.toJSON cfg.research.protonManifest}
    ''
    + lib.optionalString (cfg.research.enable && cfg.research.liveLaunch) ''
      research_live_launch = true
    '';

    systemd.tmpfiles.rules = lib.optional cfg.research.enable "d ${campaignDir} 0700 ${cfg.user} users -";

    # The immutable dispatcher stays in the system closure and is referenced from /etc, without
    # touching Steam's package set (which would also restart polkit and reload dbus). It is placed in
    # Steam's tool directory only by a verified, reversible operational step, and it only runs when a
    # game selects it and a campaign has armed a dispatch context.
    environment.etc."stutter/research-dispatcher" =
      lib.mkIf (cfg.research.enable && cfg.research.liveLaunch)
        {
          source = dispatcher.steamcompattool;
        };

    # Start with the system; the worker starts the controller after itself.
    systemd.targets.multi-user.wants = [ "stutter-privileged-worker@${cfg.user}.service" ];
  };
}
