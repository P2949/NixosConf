{ pkgs, ... }:

let
  unrealFhs =
    (pkgs.steam.override {
      extraPkgs =
        pkgs: with pkgs; [
          nss
          nspr
        ];
    }).run;

  unrealEngine = pkgs.writeShellScriptBin "unreal-engine" ''
    UE_ROOT="$HOME/Development/Unreal/Engines/UE_5.8.2"

    if [[ ! -x "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" ]]; then
      echo "Unreal Engine 5.8.2 not found at:"
      echo "  $UE_ROOT"
      exit 1
    fi

    exec ${unrealFhs}/bin/steam-run \
      "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" \
      "$@"
  '';
in
{
  home.packages = [
    unrealFhs
    unrealEngine
  ];
}
