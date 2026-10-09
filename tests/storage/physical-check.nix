{ pkgs }:
pkgs.runCommand "check-granular-physical-markers"
  {
    nativeBuildInputs = [ pkgs.python3 ];
    PHYSICAL_CHECK_SOURCE = ../../scripts/granular-physical-check.py;
  }
  ''
    python ${./test_physical_check.py}
    touch "$out"
  ''
