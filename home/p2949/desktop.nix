{ pkgs, ... }:

{
  home.packages = with pkgs; [
    # Terminal / launcher / file manager
    alacritty
    thunar
    fuzzel

    # Desktop shell
    waybar
    mako

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

  # Hyprland itself remains a NixOS/system responsibility.
  # Home Manager owns only its per-user configuration.
  xdg.configFile."hypr/hyprland.lua".source =
    ./hyprland.lua;

  # hyprpolkitagent installs its executable under libexec rather than bin.
  # Manage it as a graphical-session systemd user service, matching
  # upstream's intended UWSM/systemd setup.
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
