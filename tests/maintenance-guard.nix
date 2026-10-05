{ pkgs }:
pkgs.runCommand "check-maintenance-guard"
  {
    nativeBuildInputs = [
      pkgs.bash
      pkgs.shellcheck
    ];
  }
  ''
    bash -n ${../modules/storage/btrfs-maintenance/guard.sh}
    shellcheck ${../modules/storage/btrfs-maintenance/guard.sh}
    cat > systemctl-stub <<'STUB'
    #!/usr/bin/env bash
    if [[ "$STATE" == unavailable ]]; then exit 1; fi
    printf '%s\n' "$STATE"
    STUB
    cat > btrfs-stub <<'STUB'
    #!/usr/bin/env bash
    case "$SCRUB" in
      clean) printf 'Status: finished\nError summary: no errors found\n' ;;
      running) printf 'Status: running\nError summary: no errors found\n' ;;
      corrupt) printf 'Status: finished\nError summary: 1 errors found\n' ;;
      unknown) printf 'no stats available\n' ;;
      *) exit 1 ;;
    esac
    STUB
    chmod +x systemctl-stub btrfs-stub
    patchShebangs systemctl-stub btrfs-stub
    check() {
      expected=$1
      role=$2
      export STATE=$3 SCRUB=$4
      status=0
      bash ${../modules/storage/btrfs-maintenance/guard.sh} "$role" "$PWD/systemctl-stub" "$PWD/btrfs-stub" || status=$?
      test "$status" = "$expected"
    }
    check 0 gc inactive clean
    check 1 gc active clean
    check 1 gc activating clean
    check 1 gc deactivating clean
    check 1 gc failed clean
    check 1 gc unavailable clean
    check 1 gc inactive running
    check 1 gc inactive corrupt
    check 1 gc inactive unknown
    check 1 gc inactive unavailable
    check 0 scrub inactive clean
    check 0 scrub failed clean
    check 1 scrub active clean
    check 1 scrub activating clean
    check 1 scrub unavailable clean
    touch "$out"
  ''
