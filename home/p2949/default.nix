{ ... }:

{
  imports = [
    ./desktop.nix
  ];

  home = {
    username = "p2949";
    homeDirectory = "/home/p2949";

    # This is the first Home Manager installation for this system.
    # Like system.stateVersion, don't casually change it later.
    stateVersion = "26.05";
  };

  xdg.enable = true;
}
