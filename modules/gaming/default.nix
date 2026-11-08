{
  config,
  lib,
  pkgs,
  username,
  pkgsMesa,
  ...
}:

let
  protonPackages = import ../../packages/proton { inherit pkgs; };
  protonLab = import ../../packages/proton/lab.nix {
    inherit pkgs protonPackages;
    inherit (pkgsMesa) mesa;
    mesa32 = pkgsMesa.pkgsi686Linux.mesa;
  };
  gpuProfile = import ../../packages/gamemode-gpu-profile { inherit pkgs; };
in
{
  options.programs.gamemode.gpuProfile.enable =
    lib.mkEnableOption "GameMode Gaming GPU profile ownership";
  config = {
    programs.steam = {
      enable = true;
      extraCompatPackages = with protonPackages; [
        cachyos
        cachyosV3
        ge
        em
      ];

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
      ++ [ protonLab ]
      ++ lib.optionals config.programs.gamemode.gpuProfile.enable [ gpuProfile ];
    programs.gamemode.settings.custom = lib.mkIf config.programs.gamemode.gpuProfile.enable {
      start = "${gpuProfile}/bin/gamemode-gpu-profile start";
      end = "${gpuProfile}/bin/gamemode-gpu-profile end";
    };
  };
}
