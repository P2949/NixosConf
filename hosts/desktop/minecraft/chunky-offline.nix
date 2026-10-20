{ pkgs }:
let
  upstream = pkgs.fetchurl {
    url = "https://cdn.modrinth.com/data/VfHc5JEX/versions/56xL4i2r/chunky-offline-v1.1.0.jar";
    sha512 = "12506295bba4909b8882b8e4b8802cadb648877be1ba8dfe3f7d8f9a7dbe5cbc6ff712be7d5a3f3b54cdc4190df1be005ae8bb53ae202b40173064810ffb536e";
  };
in
pkgs.runCommand "chunky-offline-v1.1.0-local.jar"
  {
    nativeBuildInputs = [
      pkgs.unzip
      pkgs.zip
    ];
  }
  ''
    unzip -q ${upstream} -d pack
    # Replace only the controller functions; retain upstream metadata and load/tick tags.
    rm -r pack/data/chunky_offline/function
    mkdir -p pack/data/chunky_offline/function
    cp ${./chunky-offline}/*.mcfunction pack/data/chunky_offline/function/
    chmod -R u+w pack
    find pack -exec touch -h -t 198001010000 {} +
    cd pack
    find . -type f | LC_ALL=C sort | zip -q -X "$out" -@
  ''
