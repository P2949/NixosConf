{ pkgs }:
pkgs.runCommand "check-activation-safety"
  {
    nativeBuildInputs = [
      pkgs.bash
      pkgs.shellcheck
      pkgs.python3
    ];
    GUARD_SOURCE = ../../../modules/storage/activation-safety/check.sh;
  }
  ''
    bash -n "$GUARD_SOURCE"
    shellcheck -s bash "$GUARD_SOURCE"
    python ${./test_guard.py}
    touch "$out"
  ''
