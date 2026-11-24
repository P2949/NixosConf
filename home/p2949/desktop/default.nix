{ pkgs, ... }:

{
  imports = [
    ./appearance.nix
    ./hyprland.nix
    ./waybar.nix
    ./notifications.nix
    ./fuzzel.nix
    ./alacritty.nix
  ];

  programs.obs-studio.enable = true;

  home.packages = with pkgs; [
    # File manager
    thunar

    # Wayland utilities
    wl-clipboard
    grim
    slurp

    # Desktop utilities
    brightnessctl
    pavucontrol

    # Multimedia
    kdePackages.kdenlive
    ffmpeg-full
    libva-utils

    # Gaming
    prismlauncher

  ];
}
