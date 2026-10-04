{ inputs, pkgs, ... }:

let
  unstable = import inputs.nixpkgs-unstable {
    system = pkgs.stdenv.hostPlatform.system;

    config = {
      allowUnfree = true;
    };
  };
in
{
  home.packages = [
    unstable.pkgsRocm.blender
  ];
}
