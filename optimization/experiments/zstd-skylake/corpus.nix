{ pkgs }:

let
  archive = pkgs.fetchurl {
    url = "https://sun.aei.polsl.pl/~sdeor/corpus/silesia.zip";
    hash = "sha256-BibiX0XA/7XcgB8Tt8gqO3V0O6B+OnGDWkHj2fY8d68=";
  };
in
pkgs.runCommand "silesia-corpus"
  {
    nativeBuildInputs = [
      pkgs.coreutils
      pkgs.findutils
      pkgs.unzip
    ];
  }
  ''
    mkdir unpacked
    unzip -q ${archive} -d unpacked

    mkdir -p "$out"

    (
      cd unpacked

      find . \
        -type f \
        -print0 \
        | sort -z \
        | xargs -0 sha256sum
    ) > "$out/files.sha256"

    : > "$out/silesia"

    while IFS= read -r -d "" file; do
      cat "$file" >> "$out/silesia"
    done < <(
      find unpacked \
        -type f \
        -print0 \
        | sort -z
    )

    sha256sum "$out/silesia" > "$out/silesia.sha256"
    wc -c < "$out/silesia" > "$out/size-bytes"

    printf '%s\n' ${archive} > "$out/archive-store-path"
  ''
