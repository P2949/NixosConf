{ lib }:
{
  package,
  march,
  mtune,
  packageAllowList,
}:
assert lib.assertMsg (lib.elem package.pname packageAllowList)
  "CPU targeting requires an explicit package allow-list";
assert lib.assertMsg (
  builtins.match "[A-Za-z0-9_-]+" march != null && builtins.match "[A-Za-z0-9_-]+" mtune != null
) "Invalid CPU target";
package.overrideAttrs (old: {
  name = "nixos-opt-cpu-${package.pname}-${march}-${mtune}-${package.version}";
  NIX_CFLAGS_COMPILE = lib.concatStringsSep " " (
    lib.filter (value: value != "") [
      (old.NIX_CFLAGS_COMPILE or "")
      "-march=${march}"
      "-mtune=${mtune}"
    ]
  );
  passthru = (old.passthru or { }) // {
    optimization = {
      stage = "cpu-codegen";
      parameters = { inherit march mtune packageAllowList; };
    };
  };
})
