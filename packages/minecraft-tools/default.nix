{
  lib,
  python3Packages,
  makeWrapper,
  btrfs-progs,
  util-linux,
}:
python3Packages.buildPythonApplication {
  pname = "minecraft-tools";
  version = "1.0.0";
  pyproject = true;
  src = ./.;
  build-system = [ python3Packages.setuptools ];
  dependencies = [ python3Packages.websockets ];
  nativeBuildInputs = [ makeWrapper ];
  postFixup = ''
    for command in minecraft-backup minecraft-prerequisites; do
      wrapProgram "$out/bin/$command" --prefix PATH : ${
        lib.makeBinPath [
          btrfs-progs
          util-linux
        ]
      }
    done
  '';
  pythonImportsCheck = [
    "minecraft_tools.backup"
    "minecraft_tools.msmp"
    "minecraft_tools.prerequisites"
    "minecraft_tools.dh_identity"
  ];
  meta.mainProgram = "minecraft-backup";
}
