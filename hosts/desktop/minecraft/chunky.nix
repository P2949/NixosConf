{ pkgs }:
let
  upstream = pkgs.fetchurl {
    url = "https://cdn.modrinth.com/data/fALzjamp/versions/4Eotm6ov/Chunky-Fabric-1.5.3.jar";
    sha512 = "b83bfe7b218d0aa6232af977ae741dc1f82b10e50cd12bb759f65cf416b8b62beccb543e587ef0b9670abe03815660f8e091bc6823624d65cf07300571573516";
  };
  # This source recompiles to the original class's exact javap disassembly.
  generationTaskSource = pkgs.fetchurl {
    url = "https://raw.githubusercontent.com/pop4959/Chunky/f57c4fa5ef08a70733ae41e4ba009cd257227a8e/common/src/main/java/org/popcraft/chunky/GenerationTask.java";
    hash = "sha256-YXL0P8GBwf3WBlVQUtURfdb8Hu1PnU7opYdIgm3vHMI=";
  };
in
pkgs.runCommand "Chunky-Fabric-1.5.3-retirement.jar"
  {
    nativeBuildInputs = [
      pkgs.jdk25
      pkgs.unzip
      pkgs.zip
      pkgs.patch
      pkgs.diffutils
    ];
    passthru = { inherit upstream generationTaskSource; };
  }
  ''
    cp ${generationTaskSource} GenerationTask.java
    chmod u+w GenerationTask.java
    mkdir original patched
    javac --release 17 -cp ${upstream} -d original GenerationTask.java
    javap -classpath ${upstream} -c -p org.popcraft.chunky.GenerationTask > upstream.bytecode
    javap -classpath original -c -p org.popcraft.chunky.GenerationTask > rebuilt.bytecode
    diff -u upstream.bytecode rebuilt.bytecode
    patch -p1 < ${./chunky-retirement.patch}
    javac --release 17 -cp ${upstream} -d patched GenerationTask.java
    unzip -q ${upstream} -d pack
    cp patched/org/popcraft/chunky/GenerationTask.class pack/org/popcraft/chunky/
    chmod -R u+w pack
    find pack -exec touch -h -t 198001010000 {} +
    cd pack
    find . -type f | LC_ALL=C sort | zip -q -X "$out" -@
  ''
