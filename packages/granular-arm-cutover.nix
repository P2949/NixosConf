{
  pkgs,
  username,
  config,
}:
let
  shutdownCutover = import ./granular-shutdown-cutover.nix { inherit pkgs username config; };
  homeAcceptance = pkgs.writeShellApplication {
    name = "granular-home-acceptance";
    text = ''
      exec ${pkgs.python3}/bin/python3 ${../scripts/granular-home-acceptance.py}
    '';
  };
in
pkgs.writeShellApplication {
  name = "granular-arm-cutover";
  runtimeInputs = [
    pkgs.coreutils
    pkgs.jq
    pkgs.gawk
    pkgs.util-linux
    pkgs.systemd
    pkgs.nixos-rebuild-ng
  ];
  text = ''
    desktop_uid=$(id -u ${pkgs.lib.escapeShellArg username})
    coreutils=${pkgs.coreutils}
    shutdown_cutover=${shutdownCutover}
    home_acceptance=${homeAcceptance}
    ${builtins.readFile ../scripts/granular-arm-cutover.sh}
  '';
}
