{
  config,
  pkgs,
  pkgsUnstable,
  ...
}:

let
  androidUserHome = "${config.home.homeDirectory}/.android";
  androidAvdHome = "${androidUserHome}/avd";
  # Current SDK libraries follow XDG_CONFIG_HOME while the emulator still
  # defaults to ~/.android. Keep both on the same explicitly retained state.
  androidStudio = pkgs.symlinkJoin {
    name = "android-studio-persistent-state-${pkgsUnstable.android-studio.version}";
    paths = [ pkgsUnstable.android-studio ];
    nativeBuildInputs = [ pkgs.makeWrapper ];
    inherit (pkgsUnstable.android-studio) meta;
    postBuild = ''
      wrapProgram "$out/bin/android-studio" \
        --set ANDROID_USER_HOME "${androidUserHome}" \
        --set ANDROID_AVD_HOME "${androidAvdHome}"
    '';
  };
in
{
  home.sessionVariables = {
    ANDROID_USER_HOME = androidUserHome;
    ANDROID_AVD_HOME = androidAvdHome;
  };

  # Studio's FHS environment supports an SDK managed in writable ~/Android/Sdk.
  home.packages = [
    # Stable Nixpkgs' Panda 4 cannot sync the real project's AGP 9.3 toolchain.
    # Use the stable Studio channel from our existing pinned unstable input.
    androidStudio
    pkgs.android-tools
  ];
}
