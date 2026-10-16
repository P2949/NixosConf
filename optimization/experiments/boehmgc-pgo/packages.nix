{ pkgs }:
let
  inherit (pkgs) lib;
  matched = import ../boehmgc-thinlto/packages.nix { inherit pkgs; };
  instrument =
    id: control:
    control.overrideAttrs (old: {
      name = "nixos-opt-pgo-boehm-gc-${id}-instrumented-${old.version}";
      NIX_CFLAGS_COMPILE =
        (old.NIX_CFLAGS_COMPILE or "") + " -fprofile-instr-generate -fprofile-update=atomic";
      # NIX_CFLAGS_COMPILE reaches the Clang driver during linking too.
      # NIX_LDFLAGS is for raw linker options, not Clang profile switches.
      preCheck = (old.preCheck or "") + ''
        # Upstream test profiles are never training inputs.
        mkdir -p "$TMPDIR/upstream-profiles"
        export LLVM_PROFILE_FILE="$TMPDIR/upstream-profiles/%p-%m.profraw"
      '';
      postCheck = (old.postCheck or "") + ''
        unset LLVM_PROFILE_FILE
      '';
      postInstall = (old.postInstall or "") + ''
        ${pkgs.llvmPackages.llvm}/bin/llvm-nm --defined-only "$out/lib/libgc.so" > "$audit/instrumentation-symbols.txt"
        grep -q __llvm_profile_write_file "$audit/instrumentation-symbols.txt"
      '';
    });
  controls = {
    generic = matched.variants.clang-stock;
    skylake = matched.variants.clang-cpu;
  };
  instrumented = lib.mapAttrs instrument controls;
  commands = lib.mapAttrs (
    _: package:
    pkgs.writeShellApplication {
      name = "nix-evaluation-pgo-training";
      text = ''
        : "''${LLVM_PROFILE_FILE:?an explicit training profile destination is required}"
        unset LD_PRELOAD LD_AUDIT
        export LD_LIBRARY_PATH=${package}/lib
        exec ${matched.consumer}/bin/nix "$@"
      '';
    }
  ) instrumented;
in
{
  inherit controls instrumented commands;
  inherit (matched) consumer;
  profileTools = pkgs.llvmPackages.llvm;
}
