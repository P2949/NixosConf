{ pkgs }:
pkgs.runCommand "check-ephemeral-root-shell"
  {
    nativeBuildInputs = [
      pkgs.bash
      pkgs.shellcheck
    ];
  }
  ''
    bash -n ${./reset.sh}
    shellcheck -s bash ${./reset.sh}
    touch "$out"
  ''
