{ pkgs, ... }:

{
  hardware.graphics = {
    enable = true;
    enable32Bit = true;
  };

  security.rtkit.enable = true;

  services.pulseaudio.enable = false;

  services.pipewire = {
    enable = true;

    alsa = {
      enable = true;
      support32Bit = true;
    };

    pulse.enable = true;
  };

  # Hyprland itself.
  programs.hyprland = {
    enable = true;

    # Recommended systemd/session integration.
    withUWSM = true;

    # Keep normal integrated XWayland for the initial workstation.
    xwayland.enable = true;
  };

  # Hyprland's portal, rather than xdg-desktop-portal-wlr.
  xdg.portal = {
    enable = true;

    extraPortals = with pkgs; [
      xdg-desktop-portal-gtk
    ];
  };

  services.udisks2.enable = true;
  services.gvfs.enable = true;

  programs.firefox.enable = true;

  programs.steam.enable = true;
  programs.gamemode.enable = true;

  programs.nix-ld.enable = true;

  environment.systemPackages = with pkgs; [
    # Core Hyprland desktop
    alacritty
    thunar
    fuzzel

    waybar
    mako
    hyprpolkitagent

    wl-clipboard

    grim
    slurp

    brightnessctl
    pavucontrol

    # Useful desktop debugging
    vulkan-tools
    mesa-demos

    # Gaming
    gamescope
    mangohud

    # Work
    vscode
  ];

  environment.sessionVariables = {
    NIXOS_OZONE_WL = "1";
  };
}
