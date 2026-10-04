{ pkgs, ... }:

{
  gtk = {
    enable = true;
    colorScheme = "dark";
  };

  home.pointerCursor = {
    enable = true;

    package = pkgs.adwaita-icon-theme;
    name = "Adwaita";
    size = 24;

    gtk.enable = true;
  };
}
