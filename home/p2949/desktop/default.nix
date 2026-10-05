{ pkgs, ... }:

{
  imports = [
    ./appearance.nix
    ./hyprland.nix
    ./waybar.nix
    ./notifications.nix
    ./fuzzel.nix
  ];

  home.packages = with pkgs; [
    # Terminal / launcher / file manager
    alacritty
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
