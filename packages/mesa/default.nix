# Backport only Mesa's pinned source onto the stable host ABI. The upstream
# package set's LLVM requires GLIBC_2.44 and cannot load in this 2.42 desktop.
{ pkgs, nixpkgsMesa }:
let
  backport =
    stable:
    let
      source = import (nixpkgsMesa + "/pkgs/development/libraries/mesa/common.nix") {
        inherit (stable) lib fetchFromGitLab;
      };
    in
    stable.mesa.overrideAttrs (old: {
      inherit (source) version src;
      mesonFlags = old.mesonFlags ++ [ "-Db_ndebug=true" ];
    });
in
{
  mesa = backport pkgs;
  pkgsi686Linux.mesa = backport pkgs.pkgsi686Linux;
}
