{
  config,
  lib,
  pkgs,
  username,
  ...
}:

{
  programs.steam = {
    enable = true;

    extraPackages = with pkgs; [
      pulseaudio
      gamemode
    ];
  };

  programs.gamemode = {
    enable = true;
    # Preserve the stock kernel mitigation during gaming sessions too.
    settings.general.disable_splitlock = 0;
  };

  # Upstream polkit helper rules authorize this group, not wheel membership.
  users.users.${username}.extraGroups = lib.optionals config.programs.gamemode.enable [
    "gamemode"
  ];

  environment.systemPackages = with pkgs; [
    gamescope
    mangohud
  ];
}
