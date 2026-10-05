{ pkgs, src }:
let
  liquidctl = import ../packages/liquidctl-pr886.nix { inherit pkgs src; };
  python = pkgs.python3.withPackages (_: [ liquidctl.pythonPackage ]);
in
pkgs.runCommand "check-commander-core-python"
  {
    nativeBuildInputs = [
      python
      pkgs.ruff
    ];
    KEEPER_SOURCE = ../modules/hardware/commander-core/keeper.py;
  }
  ''
    export PYTHONPYCACHEPREFIX="$TMPDIR/pycache"
    export XDG_RUNTIME_DIR="$TMPDIR/runtime"
    mkdir -m 0700 "$XDG_RUNTIME_DIR"
      python -m py_compile "$KEEPER_SOURCE" ${./test_commander_core.py}
      ruff check "$KEEPER_SOURCE" ${./test_commander_core.py}
      python ${./test_commander_core.py} -v
      touch "$out"
  ''
