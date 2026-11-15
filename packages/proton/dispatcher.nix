# Steam compatibility tool whose `proton` entry forwards Steam's exact verb and arguments to
# Stutter's research dispatcher. It does not choose a Proton itself: the resident controller arms
# one-use tickets and a per-campaign context directory, and the dispatcher re-attests the Steam
# client, the installed tool and the ticket before it executes the selected Proton.
#
# The tool is immutable and exact: it names the pinned Stutter binary by store path, so a changed
# binary is a different derivation and nothing can swap the implementation between a campaign's
# freeze and its launch. `runtimeAppId` must be the Steam Linux Runtime that the selected Proton
# builds declare in their own toolmanifest.vdf (the four Nix builds all require 4183110); a mismatch
# would run the real Proton inside the wrong container.
{
  lib,
  runCommand,
  writeText,
}:
{
  stutterBinary,
  studyDir,
  runtimeAppId ? "4183110",
}:
assert lib.assertMsg (
  builtins.match "/[A-Za-z0-9_+./-]+" studyDir != null && !(lib.hasInfix ".." studyDir)
) "studyDir must be a plain absolute path";
assert lib.assertMsg (
  builtins.match "[0-9]+" runtimeAppId != null
) "runtimeAppId must be a Steam application id";
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
      "require_tool_appid" "${runtimeAppId}"
      "use_tool_subprocess_reaper" "1"
    }
  '';
in
runCommand id
  {
    outputs = [
      "out"
      "steamcompattool"
    ];
    passthru = { inherit id; };
  }
  ''
    echo 'Use programs.steam.extraCompatPackages; the tool is in steamcompattool.' > "$out"
    mkdir -p "$steamcompattool"
    cp ${vdf} "$steamcompattool/compatibilitytool.vdf"
    cp ${manifest} "$steamcompattool/toolmanifest.vdf"
    cat > "$steamcompattool/proton" <<'SH'
    #!/bin/sh
    ctx=$(ls -dt ${studyDir}/*/dispatch 2>/dev/null | head -1)
    [ -n "$ctx" ] || { echo "no armed research campaign" >&2; exit 1; }
    exec ${stutterBinary} research dispatch --context-dir "$ctx" -- "$0" "$@"
    SH
    chmod 0555 "$steamcompattool/proton"
  ''
