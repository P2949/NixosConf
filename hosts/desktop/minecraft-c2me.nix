{ pkgs }:
# Official Fabric / Minecraft 26.3 release metadata and fabric.mod.json verified
# on 2026-10-12. This artifact is a qualification candidate, pending acceptance.
pkgs.fetchurl {
  url = "https://cdn.modrinth.com/data/VSNURh3q/versions/ODMLK8M9/c2me-fabric-mc26.3-0.4.2-alpha.0.90.jar";
  hash = "sha256-aciaAUsSQo5cizz/HQD3jsAUH85fOZerGnDugWiZkpE=";
}
