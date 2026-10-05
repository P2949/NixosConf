{ config, pkgs, ... }:
let
  guard =
    mode:
    "${pkgs.bash}/bin/bash ${./maintenance-guard.sh} ${mode} ${config.systemd.package}/bin/systemctl ${pkgs.btrfs-progs}/bin/btrfs";
in
{
  nix.gc = {
    automatic = true;
    dates = "Sat *-*-* 04:00:00";
    persistent = false;
    options = "--delete-older-than 30d";
  };
  # Ordering covers simultaneous queued jobs; the condition covers an already
  # running scrub and refuses GC when its most recent health is unknown/bad.
  systemd.services.nix-gc = {
    after = [ "btrfs-scrub--.service" ];
    serviceConfig.ExecCondition = guard "gc";
  };
  services.journald.extraConfig = ''
    SystemMaxUse=2G
    SystemKeepFree=4G
    MaxRetentionSec=90day
  '';
  systemd.coredump.settings.Coredump = {
    Storage = "external";
    Compress = true;
    ProcessSizeMax = "32G";
    ExternalSizeMax = "8G";
    MaxUse = "4G";
    KeepFree = "4G";
  };
}
