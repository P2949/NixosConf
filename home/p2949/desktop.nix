{ pkgs, ... }:

{
  home.packages = with pkgs; [
    # Terminal / launcher / file manager
    alacritty
    thunar
    fuzzel

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

  xdg.configFile."hypr/hyprland.lua".source =
    ./hyprland.lua;

  programs.waybar = {
    enable = true;
    systemd.enable = true;
  };

  services.mako.enable = true;

  systemd.user.services.hyprpolkitagent = {
    Unit = {
      Description = "Hyprland Polkit Authentication Agent";
      PartOf = [ "graphical-session.target" ];
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      ExecStart =
        "${pkgs.hyprpolkitagent}/libexec/hyprpolkitagent";

      Slice = "session.slice";
      TimeoutStopSec = "5s";
      Restart = "on-failure";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
