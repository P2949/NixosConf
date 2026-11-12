# Candidate Steam compatibility tool whose `proton` entry forwards Steam's exact verb and arguments
# to Stutter's research dispatcher. It does not choose a Proton itself: the resident controller arms
# one-use tickets and a context directory, and the dispatcher re-attests the installed tool before
# exec. This is a proposal that needs a real Steam preflight (pressure-vessel mounts of the store
# and the context directory); it must not be installed globally until that qualification passes.
{
  lib,
  runCommand,
  writeText,
}:
{
  stutterBinary,
  contextDir,
}:
assert lib.assertMsg (
  builtins.match "/[A-Za-z0-9_+./-]+" contextDir != null && !(lib.hasInfix ".." contextDir)
) "contextDir must be a plain absolute path";
let
  id = "stutter-research-dispatcher";
  vdf = writeText "compatibilitytool.vdf" ''
    "compatibilitytools"
    {
      "compat_tools"
      {
        "${id}"
        {
          "install_path" "."
          "display_name" "Stutter Research Dispatcher"
          "from_oslist" "windows"
          "to_oslist" "linux"
        }
      }
    }
  '';
  manifest = writeText "toolmanifest.vdf" ''
    "manifest"
    {
      "version" "2"
      "commandline" "/proton %verb%"
      "require_tool_appid" "1628350"
      "use_tool_subprocess_reaper" "1"
    }
  '';
in
runCommand id { passthru = { inherit id; }; } ''
  mkdir -p "$out"
  cp ${vdf} "$out/compatibilitytool.vdf"
  cp ${manifest} "$out/toolmanifest.vdf"
  cat > "$out/proton" <<'SH'
  #!/bin/sh
  exec ${stutterBinary} research dispatch --context-dir ${contextDir} -- "$0" "$@"
  SH
  chmod 0555 "$out/proton"
''
