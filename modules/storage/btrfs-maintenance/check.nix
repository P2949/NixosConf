{ pkgs }:
pkgs.runCommand "check-btrfs-maintenance-shell"
  {
    nativeBuildInputs = [
      pkgs.bash
      pkgs.shellcheck
    ];
  }
  ''
    bash -n ${./guard.sh}
    shellcheck -s bash ${./guard.sh}
    touch "$out"
  ''
