{ pkgs }:
pkgs.runCommand "check-granular-home-acceptance"
  {
    nativeBuildInputs = [ pkgs.python3 ];
    HOME_ACCEPTANCE_SOURCE = ../../scripts/granular-home-acceptance.py;
  }
  ''
    python ${./test_home_acceptance.py}
    touch "$out"
  ''
