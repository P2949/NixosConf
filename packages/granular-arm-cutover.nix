{
  pkgs,
  username,
  config,
}:
let
  shutdownCutover = import ./granular-shutdown-cutover.nix { inherit pkgs username config; };
in
pkgs.writeShellApplication {
  name = "granular-arm-cutover";
  runtimeInputs = [
    pkgs.coreutils
    pkgs.jq
    pkgs.gawk
    pkgs.util-linux
    pkgs.systemd
    pkgs.nixos-rebuild
  ];
  text = ''
    desktop_uid=$(id -u ${pkgs.lib.escapeShellArg username})
    coreutils=${pkgs.coreutils}
    shutdown_cutover=${shutdownCutover}
    ${builtins.readFile ../scripts/granular-arm-cutover.sh}
  '';
}
