{
  pkgs,
  repository ? null,
}:
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
  allVariants = {
    gcc-stock = gcc.stock;
    gcc-cpu = gcc.candidate;
  }
  // variants;
  commands = {
    gcc-stock = gcc.stockCommand;
    gcc-cpu = gcc.candidateCommand;
  }
  // lib.mapAttrs (
    _: package:
    pkgs.writeShellApplication {
      name = "nix-evaluation";
      text = ''
        unset LD_PRELOAD LD_AUDIT
        export LD_LIBRARY_PATH=${package}/lib
        exec ${gcc.consumer}/bin/nix "$@"
      '';
    }
  ) variants;
  manifest =
    assert repository != null && repository ? rev;
    pkgs.writeText "boehmgc-thinlto-functional-matrix.json" (
      builtins.unsafeDiscardStringContext (
        builtins.toJSON {
          schemaVersion = 1;
          kind = "boehmgc-thinlto-functional-matrix";
          acceptance = "FUNCTIONAL_ONLY_NOT_PERFORMANCE";
          sourceRevision = repository.rev;
          sourceNarHash = repository.narHash;
          collectorPolicy = {
            enableLargeConfig = true;
            initialMarkStackSize = 1048576;
          };
          consumer = {
            output = toString gcc.consumer;
            derivation = gcc.consumer.drvPath;
            inherit (gcc.consumer) version;
          };
          variants = lib.mapAttrs (
            id: package:
            let
              compiler = if lib.hasPrefix "gcc-" id then pkgs.stdenv.cc else clang;
              linker = if lib.hasPrefix "gcc-" id then pkgs.stdenv.cc.bintools else llvm.bintools;
              tool = value: {
                output = toString value;
                derivation = value.drvPath;
                version = value.version;
              };
            in
            {
              output = toString package;
              derivation = package.drvPath;
              command = toString commands.${id};
              audit = if package ? audit then toString package.audit else null;
              compiler = tool compiler;
              linker = tool linker;
              source = {
                output = toString package.src;
                derivation = package.src.drvPath;
                narHash = package.src.outputHash;
              };
              inherit (package) version configureFlags makeFlags;
              compileFlags = package.NIX_CFLAGS_COMPILE or "";
              linkFlags = package.NIX_LDFLAGS or "";
              cpuTarget = lib.elem id [
                "gcc-cpu"
                "clang-cpu"
                "clang-cpu-thinlto"
              ];
              thinLTO = lib.hasSuffix "thinlto" id;
            }
          ) allVariants;
          comparisons = {
            gccCpu = [
              "gcc-stock"
              "gcc-cpu"
            ];
            clangCpu = [
              "clang-stock"
              "clang-cpu"
            ];
            thinLTO = [
              "clang-stock"
              "clang-thinlto"
            ];
            cpuThinLTO = [
              "clang-cpu"
              "clang-cpu-thinlto"
            ];
            # This bridge changes compiler AND linker; it cannot isolate LTO.
            toolchainBridge = [
              "gcc-stock"
              "clang-stock"
            ];
          };
        }
      )
      + "\n"
    );
in
{
  inherit
    variants
    allVariants
    commands
    manifest
    ;
  gccStock = gcc.stock;
  gccCpu = gcc.candidate;
  consumer = gcc.consumer;
}
