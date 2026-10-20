{ pkgs }:
pkgs.runCommand "check-gpu-policy"
  { nativeBuildInputs = [ (pkgs.python3.withPackages (ps: [ ps.pyyaml ])) ]; }
  ''
    export PYTHONDONTWRITEBYTECODE=1
    python3 ${./test_policy.py} ${../../../hosts/desktop/lact-policy.yaml}
    touch "$out"
  ''
