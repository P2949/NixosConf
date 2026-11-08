{ pkgs }:
let
  sources = import ./sources.nix;
  build = pkgs.callPackage ./compat-tool.nix { };
in
builtins.mapAttrs (_: source: build source) sources
