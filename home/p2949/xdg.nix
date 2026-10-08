{ config, ... }:

{
  xdg = {
    enable = true;

    # Reconstruct the observed MIME association instead of bind-mounting a
    # mutable file that GIO needs to replace atomically.
    mimeApps = {
      enable = true;
      associations.added."text/markdown" = [ "code.desktop" ];
    };

    userDirs = {
      enable = true;
      createDirectories = true;

      desktop = "${config.home.homeDirectory}/Desktop";
      documents = "${config.home.homeDirectory}/Documents";
      download = "${config.home.homeDirectory}/Downloads";
      music = "${config.home.homeDirectory}/Music";
      pictures = "${config.home.homeDirectory}/Pictures";

      # Keep the existing development tree instead of introducing ~/Projects.
      projects = "${config.home.homeDirectory}/Development";

      publicShare = "${config.home.homeDirectory}/Public";
      templates = "${config.home.homeDirectory}/Templates";
      videos = "${config.home.homeDirectory}/Videos";
    };
  };
}
