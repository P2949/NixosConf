{ pkgs, username, config }:
let
  settings = pkgs.writeText "granular-physical-check-settings.json" (builtins.toJSON {
    inherit username;
    home = config.users.users.${username}.home;
    caches = pkgs.lib.concatMap (entry: map (child: "${entry.parent}/${child}") entry.children)
      config.workstation.ephemeralHomeDirectories.paths;
  });
in
pkgs.writeShellApplication {
  name = "granular-physical-check";
  runtimeInputs = [ pkgs.util-linux ];
  text = ''
    exec ${pkgs.python3}/bin/python3 ${../scripts/granular-physical-check.py} ${settings} "$@"
  '';
}
