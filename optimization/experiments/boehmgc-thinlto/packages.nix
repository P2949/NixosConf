{ pkgs }:
let
  inherit (pkgs) lib;
  gcc = import ../boehmgc-nix-evaluation/packages.nix { inherit pkgs; };
  llvm = pkgs.llvmPackages;
  # Keep the C++ ABI while selecting LLVM's linker and bitcode-aware tools.
  clang = llvm.clang.override { bintools = llvm.bintools; };
  clangStdenv = pkgs.overrideCC pkgs.stdenv clang;
  clangBase = pkgs.boehmgc.override {
    stdenv = clangStdenv;
    enableLargeConfig = true;
    initialMarkStackSize = 1048576;
  };
  mkVariant =
    {
      id,
      cpuTarget,
      thinLTO,
    }:
    let
      base =
        if cpuTarget then
          import ../../stages/cpu-codegen.nix { inherit lib; } {
            package = clangBase;
            march = "skylake";
            mtune = "skylake";
            packageAllowList = [ "boehm-gc" ];
          }
        else
          clangBase;
    in
    assert base.pname == "boehm-gc";
    assert clangStdenv.hostPlatform.system == "x86_64-linux";
    base.overrideAttrs (old: {
      name = "nixos-opt-lto-boehm-gc-${id}-${old.version}";
      outputs = lib.unique ((old.outputs or [ "out" ]) ++ [ "audit" ]);
      NIX_CFLAGS_COMPILE = (old.NIX_CFLAGS_COMPILE or "") + lib.optionalString thinLTO " -flto=thin";
      # Identical diagnostic linker flags in both matched Clang controls.
      NIX_LDFLAGS = (old.NIX_LDFLAGS or "") + " --save-temps";
      postBuild =
        (old.postBuild or "")
        + ''
          mkdir compiler-audit
          ${clang}/bin/clang --version > compiler-audit/compiler-version.txt
          ${llvm.bintools}/bin/ld --version > compiler-audit/linker-version.txt
          grep -q '^LLD ' compiler-audit/linker-version.txt
          object=$(find . -type f -path '*/.libs/*' \( -name alloc.o -o -name '*-alloc.o' -o -name gc.o -o -name '*-gc.o' \) | sort | head -n 1)
          test -n "$object"
          ${pkgs.file}/bin/file -b "$object" > compiler-audit/object-format.txt
          sha256sum "$object" > compiler-audit/object-sha256.txt
        ''
        + lib.optionalString thinLTO ''
          grep -q 'LLVM IR bitcode' compiler-audit/object-format.txt
          ${llvm.llvm}/bin/llvm-bcanalyzer -dump "$object" > compiler-audit/bitcode.txt
          grep -q GLOBALVAL_SUMMARY_BLOCK compiler-audit/bitcode.txt
          find . -type f -name '*.index.bc' | sort > compiler-audit/thin-link-indexes.txt
          test -s compiler-audit/thin-link-indexes.txt
        ''
        + lib.optionalString (!thinLTO) ''
          grep -q 'ELF 64-bit' compiler-audit/object-format.txt
        '';
      postInstall = (old.postInstall or "") + ''
        mkdir -p "$audit"
        cp compiler-audit/* "$audit/"
      '';
      passthru = (old.passthru or { }) // {
        compilerExperiment = {
          inherit id cpuTarget thinLTO;
          compiler = clang;
          linker = llvm.bintools;
        };
      };
    });
  variants = {
    clang-stock = mkVariant {
      id = "clang-stock";
      cpuTarget = false;
      thinLTO = false;
    };
    clang-cpu = mkVariant {
      id = "clang-cpu";
      cpuTarget = true;
      thinLTO = false;
    };
    clang-thinlto = mkVariant {
      id = "clang-thinlto";
      cpuTarget = false;
      thinLTO = true;
    };
    clang-cpu-thinlto = mkVariant {
      id = "clang-cpu-thinlto";
      cpuTarget = true;
      thinLTO = true;
    };
  };
in
{
  inherit variants;
  gccStock = gcc.stock;
  gccCpu = gcc.candidate;
  consumer = gcc.consumer;
}
