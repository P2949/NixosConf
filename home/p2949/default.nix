{ username, ... }:

{
  imports = [
    ./cli.nix
    ./desktop
    ./development
    ./persistence.nix
    ./shell.nix
    ./xdg.nix
  ];

  home = {
    inherit username;
    homeDirectory = "/home/${username}";

    # This is the first Home Manager installation for this system.
    # Like system.stateVersion, don't casually change it later.
    stateVersion = "26.05";
  };

}
