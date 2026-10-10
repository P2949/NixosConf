{ ... }:

{
  nix.gc = {
    automatic = true;
    dates = "Sat *-*-* 04:00:00";
    persistent = false;
    options = "--delete-older-than 30d";
  };

  services.journald.extraConfig = ''
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
