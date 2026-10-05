{
  config,
  lib,
  pkgs,
  ...
}:

let
  # Keep the accepted store identity while organizing the source filename.
  guardSource = builtins.path {
    path = ./guard.sh;
    name = "maintenance-guard.sh";
  };
  guard =
    mode:
    "${pkgs.bash}/bin/bash ${guardSource} ${mode} ${config.systemd.package}/bin/systemctl ${pkgs.btrfs-progs}/bin/btrfs";
in
{
  assertions = [
    {
      assertion = config.nix.gc.automatic;
      message = "Btrfs maintenance coordination requires automatic Nix GC.";
    }
    {
      assertion =
        config.services.btrfs.autoScrub.enable
        && builtins.elem "/" config.services.btrfs.autoScrub.fileSystems;
      message = "Btrfs maintenance coordination requires a configured scrub of /.";
    }
  ];

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
