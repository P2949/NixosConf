{ pkgs }:
let
  build =
    cross: name:
    cross.stdenv.mkDerivation {
      pname = "proton-lab-fixture-${name}";
      version = "2";
      src = ./fixture.c;
      dontUnpack = true;
      dontConfigure = true;
      dontFixup = true;
      buildPhase = ''
        $CC "$src" -O2 -o probe.exe -ld3d11 -ld3d12 -ldxgi -ldxguid -lddraw -lwinmm -static
      '';
      installPhase = ''
        mkdir -p "$out/bin"
        cp probe.exe "$out/bin/probe-${name}.exe"
      '';
    };
in
{
  win64 = build pkgs.pkgsCross.mingwW64 "win64";
  win32 = build pkgs.pkgsCross.mingw32 "win32";
}
