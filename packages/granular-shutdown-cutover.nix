{
  pkgs,
  username,
  config,
}:
let
  finalSync = import ./granular-migration.nix { inherit pkgs username config; };
  physicalCheck = import ./granular-physical-check.nix { inherit pkgs username config; };
in
pkgs.writeShellApplication {
  name = "granular-shutdown-cutover";
  runtimeInputs = [
    pkgs.coreutils
    pkgs.gnugrep
    pkgs.procps
    pkgs.systemd
  ];
  text = ''
    desktop_uid=$(id -u ${pkgs.lib.escapeShellArg username})
    final_sync=${finalSync}
    physical_check=${physicalCheck}
    ${builtins.readFile ../scripts/granular-shutdown-cutover.sh}
  '';
}
