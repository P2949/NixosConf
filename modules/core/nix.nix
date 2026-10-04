{
  pkgs,
  username,
  ...
}:

{
  nixpkgs.config.allowUnfree = true;

  nix.settings = {
    experimental-features = [
      "nix-command"
      "flakes"
    ];

    trusted-users = [
      username
    ];

    auto-optimise-store = true;
  };

  nix.gc = {
    automatic = true;
    dates = "03:30";
    options = "--delete-older-than 14d";
  };

  systemd.services.nix-prune-system-generations = {
    description = "Prune old NixOS system generations";

    serviceConfig.Type = "oneshot";

    script = ''
      ${pkgs.nix}/bin/nix-env \
        --profile /nix/var/nix/profiles/system \
        --delete-generations +10
    '';
  };

  systemd.timers.nix-prune-system-generations = {
    description = "Periodically prune old NixOS system generations";
    wantedBy = [ "timers.target" ];

    timerConfig = {
      OnCalendar = "03:00";
      Persistent = true;
    };
  };
}
