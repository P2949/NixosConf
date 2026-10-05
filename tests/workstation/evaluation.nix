{ pkgs, config }:

let
  # Force toplevel evaluation (including NixOS assertions) for both boot
  # policies. Discard the string context so CI does not build either closure.
  evaluation = builtins.unsafeDiscardStringContext (
    builtins.toJSON {
      desktop = config.system.build.toplevel.drvPath;
      persistentRoot = config.specialisation.persistent-root.configuration.system.build.toplevel.drvPath;
      stateVersion = config.system.stateVersion;
    }
  );
in
pkgs.runCommand "check-desktop-evaluation" { inherit evaluation; } ''
  printf '%s\n' "$evaluation" > "$out"
''
