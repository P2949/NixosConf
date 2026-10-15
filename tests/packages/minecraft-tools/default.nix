{ pkgs }:
let
  tools = pkgs.callPackage ../../../packages/minecraft-tools { };
  python = pkgs.python3.withPackages (ps: [ ps.websockets ]);
in
pkgs.runCommand "check-minecraft-tools-python"
  {
    nativeBuildInputs = [
      python
      pkgs.jq
      pkgs.ruff
    ];
    backupClient = tools;
    managementClient = tools;
  }
  ''
    set -eu
    export PYTHONPATH="${tools}/${pkgs.python3.sitePackages}:${./.}"
    export PYTHONDONTWRITEBYTECODE=1
    ruff format --config ${../../../packages/minecraft-tools}/pyproject.toml --check ${../../../packages/minecraft-tools} ${./.}
    ruff check --config ${../../../packages/minecraft-tools}/pyproject.toml ${../../../packages/minecraft-tools} ${./.}
    python3 -m unittest discover -s ${./.} -p 'test_*.py' -v
    policy="$TMPDIR/policy.json"
    python3 -c 'import json, sys; from test_config import POLICY; p = dict(POLICY); p["source"] = sys.argv[2]+"/source"; p["stateDirectory"] = sys.argv[2]+"/state"; p["snapshotMount"] = sys.argv[2]+"/snapshots"; p["snapshotRoot"] = sys.argv[2]+"/snapshots/game"; p["runtimeDirectory"] = sys.argv[2]+"/runtime"; json.dump(p, open(sys.argv[1], "w"))' "$policy" "$TMPDIR"
          "$backupClient/bin/minecraft-backup" --help | grep -F 'status [--live]|recover-autosave'
          "$backupClient/bin/minecraft-backup" --config "$policy" status | jq -e '.managed_snapshot_count == 0'
          if "$backupClient/bin/minecraft-backup" --config "$policy" invalid-command >/dev/null 2>&1; then
            echo "minecraft-backup accepted an invalid command" >&2
            exit 1
          fi

          client="$managementClient/bin/minecraft-msmp"
          validSecret="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd"

          if [ ! -x "$client" ]; then
            echo "minecraft-msmp executable is missing" >&2
            exit 1
          fi

          helpOutput="$("$client" --help)"

          case "$helpOutput" in
            *"{validate,discover,call,save-and-wait,watch}"*)
              ;;
            *)
              echo "minecraft-msmp help output is missing expected commands" >&2
              exit 1
              ;;
          esac

          validateOutput="$(
            MINECRAFT_MANAGEMENT_SECRET="$validSecret"             "$client" --config "$policy" validate
          )"

          if [ "$validateOutput" != "configuration valid: ws://127.0.0.1:25585" ]; then
            echo "minecraft-msmp default configuration validation differed from expected output" >&2
            exit 1
          fi

          if           MINECRAFT_MANAGEMENT_SECRET="too-short"             "$client" --config "$policy" validate >/dev/null 2>&1
          then
            echo "minecraft-msmp accepted a short management secret" >&2
            exit 1
          fi

          if           MINECRAFT_MANAGEMENT_SECRET="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabc!"             "$client" --config "$policy" validate >/dev/null 2>&1
          then
            echo "minecraft-msmp accepted a non-alphanumeric management secret" >&2
            exit 1
          fi

          managementEnv="$TMPDIR/minecraft-management.env"

          printf '%s\n' 'MINECRAFT_MANAGEMENT_SECRET=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd' > "$managementEnv"

          env           -u MINECRAFT_MANAGEMENT_SECRET           MINECRAFT_MANAGEMENT_ENV_FILE="$managementEnv"           "$client" --config "$policy" validate >/dev/null

          printf '%s\n' 'MINECRAFT_MANAGEMENT_SECRET=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd' 'MINECRAFT_MANAGEMENT_SECRET=abcd0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ' > "$managementEnv"

          if           env             -u MINECRAFT_MANAGEMENT_SECRET             MINECRAFT_MANAGEMENT_ENV_FILE="$managementEnv"             "$client" --config "$policy" validate >/dev/null 2>&1
          then
            echo "minecraft-msmp accepted duplicate secret assignments" >&2
            exit 1
          fi

          if           MINECRAFT_MANAGEMENT_SECRET="$validSecret"           MINECRAFT_MANAGEMENT_URL="ws://192.0.2.1:25585"             "$client" --config "$policy" validate >/dev/null 2>&1
          then
            echo "minecraft-msmp accepted a non-loopback management endpoint" >&2
            exit 1
          fi

          if           MINECRAFT_MANAGEMENT_SECRET="$validSecret"           MINECRAFT_MANAGEMENT_URL="wss://127.0.0.1:25585"             "$client" --config "$policy" validate >/dev/null 2>&1
          then
            echo "minecraft-msmp accepted TLS despite the configured plaintext loopback endpoint" >&2
            exit 1
          fi


    for command in minecraft-backup minecraft-msmp minecraft-prerequisites minecraft-dh-identity; do
      "${tools}/bin/$command" --help >/dev/null
    done
    for command in minecraft-backup minecraft-msmp minecraft-prerequisites; do
      if "${tools}/bin/$command" >/dev/null 2>&1; then
        echo "$command accepted a missing configuration" >&2
        exit 1
      fi
    done
    touch "$out"
  ''
