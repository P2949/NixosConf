{
  config,
  lib,
  pkgs,
  ...
}:

let
  guard =
    mode:
    "${pkgs.bash}/bin/bash ${./maintenance-guard.sh} ${mode} ${config.systemd.package}/bin/systemctl ${pkgs.btrfs-progs}/bin/btrfs";
in
{
  services.btrfs.autoScrub = {
    enable = true;
    interval = "*-*-01 02:00:00";
    fileSystems = [ "/" ];
  };

  systemd.timers."btrfs-scrub--".timerConfig.AccuracySec = lib.mkForce "1min";

  # Ordering covers simultaneous queued jobs; the conditions prevent GC and
  # scrub from overlapping when either maintenance job is already running.
  # GC additionally requires the most recent scrub state to be finished and
  # clean before collection is allowed.
  systemd.services.nix-gc = {
    after = [ "btrfs-scrub--.service" ];
    serviceConfig.ExecCondition = guard "gc";
  };

  systemd.services."btrfs-scrub--".serviceConfig.ExecCondition = guard "scrub";
}
