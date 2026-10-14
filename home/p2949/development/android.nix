{ pkgs, ... }:

{
  # Studio's FHS environment supports an SDK managed in writable ~/Android/Sdk.
  home.packages = [
    pkgs.android-studio
    pkgs.android-tools
  ];
}
