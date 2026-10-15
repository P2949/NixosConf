{ pkgs, ... }:

{
  imports = [
    ./android.nix
    ./blender.nix
    ./unreal.nix
    ./unity.nix
  ];

  home.packages = [
    pkgs.clang-tools
    pkgs.nixfmt
    pkgs.vscode
  ];
}
