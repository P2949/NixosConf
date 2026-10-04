{ pkgs, ... }:

{
  programs.steam = {
    enable = true;

    extraPackages = with pkgs; [
      pulseaudio
      gamemode
    ];
  };

  programs.gamemode.enable = true;

  environment.systemPackages = with pkgs; [
    gamescope
    mangohud
  ];
}
