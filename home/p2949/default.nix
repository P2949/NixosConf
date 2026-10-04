{ username, ... }:

{
  imports = [
    ./desktop
    ./development
    ./shell.nix
  ];

  home = {
    inherit username;
    homeDirectory = "/home/${username}";

    # This is the first Home Manager installation for this system.
    # Like system.stateVersion, don't casually change it later.
    stateVersion = "26.05";
  };

  xdg.enable = true;
}
