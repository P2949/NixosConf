{ pkgs, username, ... }:

{
  programs.hyprland = {
    enable = true;
    withUWSM = true;
    xwayland.enable = true;
  };

  environment.sessionVariables = {
    NIXOS_OZONE_WL = "1";
  };
  services.greetd = {
    enable = true;
    useTextGreeter = true;

    settings = {
      # Automatic session on boot.
      initial_session = {
        command = "${pkgs.uwsm}/bin/uwsm start hyprland.desktop";
        user = username;
      };

      # If Hyprland is deliberately logged out, give us a normal
      # login screen rather than immediately logging back in.
      default_session = {
        command = "${pkgs.tuigreet}/bin/tuigreet --time --remember --remember-session";
        user = "greeter";
      };
    };
  };
}
