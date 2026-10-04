{ pkgs, ... }:

{
  imports = [
    ./blender.nix
    ./unreal.nix
  ];

  home.packages = [
    pkgs.clang-tools
    pkgs.nixfmt
  ];
}
