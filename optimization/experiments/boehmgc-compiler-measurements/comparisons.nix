{
  pkgs,
  profiles ? { },
}:
let
  inherit (pkgs) lib;
  lto = import ../boehmgc-thinlto/packages.nix { inherit pkgs; };
  pgo = import ../boehmgc-pgo/packages.nix { inherit pkgs; };
  optimized = builtins.mapAttrs (
    variant: identity:
    import ../boehmgc-pgo/optimized.nix {
      inherit pkgs variant;
      inherit (identity) profilePath profileNarHash;
    }
  ) profiles;
  pair = stock: candidate: attribution: {
    inherit stock candidate attribution;
    consumer = lto.consumer;
    packageAllowList = [ "boehm-gc" ];
    collectorPolicy = {
      enableLargeConfig = true;
      initialMarkStackSize = 1048576;
    };
  };
in
{
  clang-cpu =
    pair lto.variants.clang-stock lto.variants.clang-cpu
      "CPU code generation with matched Clang/LLD";
  thinlto =
    pair lto.variants.clang-stock lto.variants.clang-thinlto
      "ThinLTO with generic CPU code generation";
  cpu-thinlto =
    pair lto.variants.clang-cpu lto.variants.clang-cpu-thinlto
      "ThinLTO with Skylake CPU code generation";
  toolchain-bridge =
    pair lto.gccStock lto.variants.clang-stock
      "Compiler AND linker change together; cannot isolate LTO";
}
// lib.optionalAttrs (profiles ? generic) {
  pgo = pair pgo.controls.generic optimized.generic "PGO with generic CPU code generation";
}
// lib.optionalAttrs (profiles ? skylake) {
  cpu-pgo = pair pgo.controls.skylake optimized.skylake "PGO with Skylake CPU code generation";
}
