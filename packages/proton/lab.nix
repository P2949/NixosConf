{
  pkgs,
  protonPackages,
  mesa,
  mesa32,
}:
let
  features = builtins.fromJSON (builtins.readFile ./features.json);
  manifest = pkgs.writeText "proton-lab.json" (
    builtins.toJSON {
      inherit features;
      tools = builtins.mapAttrs (
        _: tool:
        tool.provenance
        // {
          path = toString tool.steamcompattool;
          source = builtins.removeAttrs tool.provenance [ "displayName" ];
        }
      ) protonPackages;
      mesa = {
        inherit (mesa) version;
        path64 = toString mesa;
        path32 = toString mesa32;
      };
      vulkan64 = "${pkgs.vulkan-tools}/bin/vulkaninfo";
      vulkan32 = "${pkgs.pkgsi686Linux.vulkan-tools}/bin/vulkaninfo";
      umu = "${pkgs.umu-launcher}/bin/umu-run";
    }
  );
in
pkgs.writeShellApplication {
  name = "proton-lab";
  runtimeInputs = [
    pkgs.python3
    pkgs.wayland-utils
  ];
  text = ''
    export PROTON_LAB_MANIFEST=${manifest}
    exec python3 ${../../scripts/proton-lab} "$@"
  '';
  passthru = { inherit manifest; };
}
