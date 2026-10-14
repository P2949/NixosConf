{ pkgs, pkgsUnstable, ... }:

{
  # Studio's FHS environment supports an SDK managed in writable ~/Android/Sdk.
  home.packages = [
    # Stable Nixpkgs' Panda 4 cannot sync the real project's AGP 9.3 toolchain.
    # Use the stable Studio channel from our existing pinned unstable input.
    pkgsUnstable.android-studio
    pkgs.android-tools
  ];
}
