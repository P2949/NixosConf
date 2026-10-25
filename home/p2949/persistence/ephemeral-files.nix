# Files cannot be individual bind mounts if their owner atomically replaces
# them. Known disposable files in persistent profiles are removed by native
# boot-only tmpfiles rules before applications start, in normal mode only.
let
  firefoxProfile = import ./firefox-profile.nix;
in
[
  {
    parent = ".codex";
    children = [
      "models_cache.json"
      "logs_2.sqlite"
      "logs_2.sqlite-wal"
      "logs_2.sqlite-shm"
    ];
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
    parent = ".config/Epic";
    children = [
      "UE4_SessionSummary_Lock"
      "UE_AnalyticsSessionSummaryManager_OrphanOwner"
      "ZenServerInstall"
      "ZenServerLaunch"
      "*AssetRegistryCacheLock"
    ];
  }
  {
    parent = ".config/mozilla/firefox";
    children = [
      "${firefoxProfile}/.parentlock"
      "${firefoxProfile}/lock"
    ];
  }
]
