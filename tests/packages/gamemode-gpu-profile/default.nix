{ pkgs }:
pkgs.runCommand "check-gamemode-gpu-profile" { nativeBuildInputs = [ pkgs.python3 ]; } ''
  export PYTHONDONTWRITEBYTECODE=1
  export GPU_HELPER_SOURCE=${../../../packages/gamemode-gpu-profile/helper.py}
  python3 ${./test_helper.py}
  touch "$out"
''
