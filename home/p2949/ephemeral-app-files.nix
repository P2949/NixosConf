# Files cannot be individual bind mounts if their owner atomically replaces
# them. Known disposable files in persistent profiles are removed by native
# boot-only tmpfiles rules before applications start, in normal mode only.
[
  {
    parent = ".codex";
    children = [ "models_cache.json" "logs_2.sqlite" "logs_2.sqlite-wal" "logs_2.sqlite-shm" ];
  }
  {
    parent = ".android";
    children = [ "adb.5037" ];
  }
  {
    parent = ".config/Code";
    children = [ "code.lock" ];
  }
  {
    parent = ".config/mozilla/firefox";
    children = [ "y34aofre.default/.parentlock" "y34aofre.default/lock" ];
  }
]
