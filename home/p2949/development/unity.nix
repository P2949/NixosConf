{ pkgs, ... }:

let
  unityHub =
    (pkgs.unityhub.override {
      extraLibs = pkgs: [
        pkgs.ncurses
      ];
    }).overrideAttrs (oldAttrs: {
      postInstall = (oldAttrs.postInstall or "") + ''
        # Unity 6000.6+ UnityShaderCompiler currently needs libtinfo.so.6.
        # Keep this workaround local to Unity Hub rather than modifying
        # the host's global library environment.
        wrapProgram "$out/opt/unityhub/unityhub" \
          --set LD_LIBRARY_PATH /usr/lib:/usr/lib64
      '';
    });
in
{
  home.packages = [
    unityHub
  ];
}
