{ pkgs }:
let
  probe =
    pkgs.runCommand "nixos-opt-pgo-fixture" { }
      ''mkdir -p "$out/bin"; echo test-only > "$out/bin/nixos-opt-fixture"'';
  system = import "${pkgs.path}/nixos/lib/eval-config.nix" {
    inherit pkgs;
    system = pkgs.stdenv.hostPlatform.system;
    modules = [
      ../../modules/workstation/optimization-boundary.nix
      {
        boot.loader.grub.devices = [ "nodev" ];
        fileSystems."/" = {
          device = "/dev/fixture";
          fsType = "ext4";
        };
        environment.systemPackages = [ probe ];
        system.stateVersion = "26.05";
      }
    ];
  };
in
system.config.system.build.toplevel
