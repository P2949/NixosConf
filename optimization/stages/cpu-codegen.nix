{ lib }:

{
  package,
  march,
  mtune ? march,
}:

package.overrideAttrs (old: {
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

      parameters = {
        inherit march mtune;
      };
    };
  };
})
