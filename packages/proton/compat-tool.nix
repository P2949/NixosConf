{
  lib,
  stdenvNoCC,
  fetchurl,
  requireFile,
  python3,
  xz,
}:
source:
stdenvNoCC.mkDerivation {
  pname = "proton-${source.id}";
  inherit (source) version;
  src =
    if source ? url then
      fetchurl {
        inherit (source) url hash;
      }
    else
      requireFile {
        inherit (source) name hash;
        message = "Restore the verified EM 11 archive with nix-store --add-fixed sha256; see docs/proton.md.";
      };
  outputs = [
    "out"
    "steamcompattool"
  ];
  nativeBuildInputs = [
    python3
    xz
  ];
  dontConfigure = true;
  dontBuild = true;
  # These are upstream Steam Runtime binaries, not host ELF executables.
  dontFixup = true;
  installPhase = ''
    runHook preInstall
    echo 'Use programs.steam.extraCompatPackages; binaries are in steamcompattool.' > "$out"
    mkdir -p "$steamcompattool"
    cp -a ./. "$steamcompattool/"
    chmod u+w "$steamcompattool/compatibilitytool.vdf"
    python3 - "$steamcompattool/compatibilitytool.vdf" <<'PY'
    import pathlib, re, sys
    path = pathlib.Path(sys.argv[1])
    text = path.read_text()
    text, keys = re.subn(r'("compat_tools"\s*\{\s*")[^"]+(")', r'\g<1>${source.id}\2', text, count=1)
    text, names = re.subn(r'("display_name"\s*")[^"]+(")', r'\g<1>${source.displayName}\2', text, count=1)
    if keys != 1 or names != 1:
        raise SystemExit('Unexpected compatibility manifest')
    path.write_text(text)
    PY
    test -x "$steamcompattool/proton"
    test -r "$steamcompattool/toolmanifest.vdf"
    runHook postInstall
  '';
  passthru.provenance = source;
  meta = {
    description = source.displayName;
    platforms = [ "x86_64-linux" ];
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
    license = lib.licenses.bsd3;
  };
}
