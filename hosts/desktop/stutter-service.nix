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
        nix-store --add-fixed sha256 /path/to/stutter/target/release/stutter
      and set services.stutterBounded.binarySha256 to the hash of that file (nix hash file --type sha256 --base16).
    '';
  };
  configDir = "/etc/stutter";
  render =
    name:
    builtins.replaceStrings
      [ "@BINARY@" "@SYSTEMCTL@" "@CONFIG_DIR@" ]
      [ "${binary}" "${config.systemd.package}/bin/systemctl" configDir ]
      (builtins.readFile "${upstream}/${name}");
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
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = builtins.match "[0-9a-f]{64}" cfg.binarySha256 != null;
        message = "services.stutterBounded.binarySha256 must be the 64 hex digit SHA-256 of the pinned binary";
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
    '';

    # Start with the system; the worker starts the controller after itself.
    systemd.targets.multi-user.wants = [ "stutter-privileged-worker@${cfg.user}.service" ];
  };
}
