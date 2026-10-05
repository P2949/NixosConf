{ pkgs, ... }:

{
  home.packages = with pkgs; [
    gh
    wget
    nano
    ripgrep
    fd
    jq
    btop
    htop
    tree
  ];
}
