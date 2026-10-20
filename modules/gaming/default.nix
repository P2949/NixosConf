{
  config,
  lib,
  pkgs,
  username,
  ...
}:

let
  gpuProfile = import ../../packages/gamemode-gpu-profile { inherit pkgs; };
in
{
  options.programs.gamemode.gpuProfile.enable =
    lib.mkEnableOption "GameMode Daily GPU profile ownership";
  config = {
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

    environment.systemPackages =
      with pkgs;
      [
        gamescope
        mangohud
      ]
      ++ lib.optionals config.programs.gamemode.gpuProfile.enable [ gpuProfile ];
    programs.gamemode.settings.custom = lib.mkIf config.programs.gamemode.gpuProfile.enable {
      start = "${gpuProfile}/bin/gamemode-gpu-profile start";
      end = "${gpuProfile}/bin/gamemode-gpu-profile end";
    };
  };
}
