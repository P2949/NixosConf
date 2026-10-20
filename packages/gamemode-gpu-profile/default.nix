{ pkgs }:
pkgs.writeShellScriptBin "gamemode-gpu-profile" ''
  exec ${pkgs.python3}/bin/python3 ${./helper.py} "$@"
''
