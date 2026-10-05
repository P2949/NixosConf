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

  home.packages = with pkgs; [
    # file manager
    thunar

    # Wayland utilities
    wl-clipboard
    grim
    slurp

    # Desktop utilities
    brightnessctl
    pavucontrol

    # Work
    vscode
  ];
}
