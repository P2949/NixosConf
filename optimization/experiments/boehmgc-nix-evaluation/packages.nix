{ pkgs }:
let
  # Preserve the GC policy used by Nix's dependency scope, including the larger
  # mark stack. CPU code generation is the only candidate variable.
  stock = pkgs.boehmgc.override {
    enableLargeConfig = true;
    initialMarkStackSize = 1048576;
  };
  candidate = import ../../stages/cpu-codegen.nix { inherit (pkgs) lib; } {
    package = stock;
    march = "skylake";
    mtune = "skylake";
    packageAllowList = [ "boehm-gc" ];
  };
in
{
  inherit stock candidate;
}
