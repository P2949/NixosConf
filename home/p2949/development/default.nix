{ lib, pkgs, ... }:

{
  imports = [
    ./blender.nix
    ./unreal.nix
    ./unity.nix
  ];

  # Keep editor ownership here; desktop composition retains the accepted
  # package ordering so this move does not rebuild the Home Manager closure.
  options.workstationHome.development.editorPackages = lib.mkOption {
    type = lib.types.listOf lib.types.package;
    default = [ ];
    internal = true;
  };
  config = {
    workstationHome.development.editorPackages = [ pkgs.vscode ];
    home.packages = [
      pkgs.clang-tools
      pkgs.nixfmt
    ];
  };
}
