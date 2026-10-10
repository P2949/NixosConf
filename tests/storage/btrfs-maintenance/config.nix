{ pkgs }:
let
  inherit (pkgs) lib;
  base = import "${pkgs.path}/nixos/lib/eval-config.nix" {
    inherit pkgs;
    system = pkgs.stdenv.hostPlatform.system;
    modules = [
      ../../../modules/storage/btrfs-maintenance
      ../../../modules/core/maintenance.nix
      {
        boot.loader.grub.devices = [ "nodev" ];
        fileSystems."/" = {
          device = "/dev/fixture";
          fsType = "btrfs";
        };
        services.btrfs.autoScrub = {
          enable = true;
          fileSystems = [ "/" ];
        };
        system.stateVersion = "26.05";
      }
    ];
  };
  accepted =
    module:
    (builtins.tryEval
      (base.extendModules { modules = [ module ]; }).config.system.build.toplevel.drvPath
    ).success;
in
assert accepted { };
assert !accepted { nix.gc.automatic = lib.mkForce false; };
assert !accepted { services.btrfs.autoScrub.enable = lib.mkForce false; };
assert !accepted { services.btrfs.autoScrub.fileSystems = lib.mkForce [ "/home" ]; };
pkgs.runCommand "check-btrfs-maintenance-config" { } ''
  echo "Btrfs maintenance configuration: one positive and three refusals passed"
  touch "$out"
''
