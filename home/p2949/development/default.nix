{ pkgs, ... }:

{
  imports = [
    ./android.nix
    ./blender.nix
    ./unreal.nix
    ./unity.nix
  ];

  programs.direnv = {
    enable = true;
    nix-direnv.enable = true;
  };

  home.packages = [
    pkgs.clang-tools
    pkgs.nixfmt
    pkgs.vscode
  ];
}
