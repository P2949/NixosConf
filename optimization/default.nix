{
  pkgs,
  inputs,
  repository,
  systemConfig,
  recoverySystem,
}:
let
  stock = import ./control/stock.nix;
  gcExperiment = import ./experiments/boehmgc-nix-evaluation/packages.nix { inherit pkgs; };
  gcThinLTO = import ./experiments/boehmgc-thinlto/packages.nix { inherit pkgs repository; };
  gcPGO = import ./experiments/boehmgc-pgo/packages.nix { inherit pkgs; };
  model = import ./experiment/model.nix { inherit (pkgs) lib; };
  gcSpecification = model.normalizeSpec (import ./experiments/boehmgc-nix-evaluation/spec.nix);
  gcCorpus = import ./corpora/nix-evaluation.nix { inherit pkgs; };
  gcBuild = import ./experiments/boehmgc-nix-evaluation/build.nix {
    inherit
      pkgs
      inputs
      repository
      systemConfig
      ;
    specification = gcSpecification;
    corpus = gcCorpus;
    packages = gcExperiment;
  };
  specification = model.normalizeSpec (import ./experiments/zstd-skylake/spec.nix);
  corpus = import ./corpora/silesia.nix { inherit pkgs; };
  candidate = import ./stages/cpu-codegen.nix { inherit (pkgs) lib; } (
    { package = pkgs.zstd; } // specification.stage.parameters
  );
  buildManifest = import ./provenance/build.nix {
    inherit
      pkgs
      inputs
      repository
      systemConfig
      specification
      corpus
      ;
    targets = {
      stock = pkgs.zstd;
      inherit candidate;
    };
  };
in
{
  packages = {
    boehmgc-pgo-instrumented = gcPGO.instrumented.generic;
    boehmgc-pgo-cpu-instrumented = gcPGO.instrumented.skylake;
    boehmgc-lto-clang-stock = gcThinLTO.variants.clang-stock;
    boehmgc-lto-clang-cpu = gcThinLTO.variants.clang-cpu;
    boehmgc-lto-clang-thinlto = gcThinLTO.variants.clang-thinlto;
    boehmgc-lto-clang-cpu-thinlto = gcThinLTO.variants.clang-cpu-thinlto;
    boehmgc-lto-matrix = gcThinLTO.manifest;
    boehmgc-lto-functional = import ./experiments/boehmgc-thinlto/functional.nix {
      inherit pkgs;
      packages = gcThinLTO;
      corpus = gcCorpus;
    };
    # Explicit experiment admission gate. Ordinary workstation applications
    # may change the desktop; measurements still require the frozen control.
    optimization-control-identity =
      pkgs.runCommand "check-optimization-control-identity"
        {
          actualLockSha256 = builtins.hashFile "sha256" (repository + "/flake.lock");
          expectedLockSha256 = stock.lockSha256;
          actualNixpkgsRevision = inputs.nixpkgs.rev;
          expectedNixpkgsRevision = stock.nixpkgsRevision;
          actualNormal = builtins.unsafeDiscardStringContext (
            toString systemConfig.config.system.build.toplevel
          );
          expectedNormal = stock.normal;
          actualPersistentRoot = builtins.unsafeDiscardStringContext (
            toString systemConfig.config.specialisation.persistent-root.configuration.system.build.toplevel
          );
          expectedPersistentRoot = stock.persistentRoot;
          actualRecoveryIso = builtins.unsafeDiscardStringContext (
            toString recoverySystem.config.system.build.isoImage
          );
          expectedRecoveryIso = stock.recoveryIso;
        }
        ''
          if [ "$actualLockSha256" != "$expectedLockSha256" ] ||
             [ "$actualNixpkgsRevision" != "$expectedNixpkgsRevision" ] ||
             [ "$actualNormal" != "$expectedNormal" ] ||
             [ "$actualPersistentRoot" != "$expectedPersistentRoot" ] ||
             [ "$actualRecoveryIso" != "$expectedRecoveryIso" ]; then
            echo "Evaluated system differs from frozen optimization control" >&2
            exit 1
          fi
          touch "$out"
        '';
    boehmgc-stock = gcExperiment.stock;
    boehmgc-cpu-target = gcExperiment.candidate;
    nix-evaluation-corpus = gcCorpus;
    nix-evaluation-spec = pkgs.writeText "nix-evaluation-specification.json" (
      builtins.toJSON gcSpecification + "\n"
    );
    nix-evaluation-build-provenance = gcBuild;
    optimization-nix-evaluation-runner = pkgs.writeShellApplication {
      name = "nixos-optimization-nix-evaluation";
      runtimeInputs = [
        pkgs.python3
        pkgs.git
        pkgs.util-linux
        pkgs.systemd
      ];
      text = ''
        export PYTHONDONTWRITEBYTECODE=1
        export PYTHONPATH=${./provenance}:${./runners}
        exec python ${./runners}/nix_evaluation.py "$@"
      '';
    };
    nix-evaluation-stock = gcExperiment.stockCommand;
    nix-evaluation-candidate = gcExperiment.candidateCommand;
    zstd-stock = pkgs.zstd;
    zstd-cpu-target = candidate;
    silesia-corpus = corpus;
    optimization-spec = pkgs.writeText "experiment-spec.json" (builtins.toJSON specification + "\n");
    optimization-build-provenance = buildManifest;
    optimization-zstd-runner = pkgs.writeShellApplication {
      name = "nixos-optimization-zstd";
      runtimeInputs = [
        pkgs.python3
        pkgs.git
        pkgs.util-linux
        pkgs.systemd
      ];
      text = ''
        export PYTHONDONTWRITEBYTECODE=1
        export PYTHONPATH=${./provenance}:${./runners}
        exec python ${./runners}/zstd.py "$@"
      '';
    };
  };
  checks = {
    boehmgc-thinlto-metadata =
      let
        metadataClosure = pkgs.closureInfo { rootPaths = [ gcThinLTO.manifest ]; };
      in
      pkgs.runCommand "check-boehmgc-thinlto-metadata-boundary" { } ''
        # Provenance strings must not retain compiler/bootstrap closures.
        test "$(wc -l < ${metadataClosure}/store-paths)" -eq 1
        grep -Fx '${gcThinLTO.manifest}' ${metadataClosure}/store-paths
        touch "$out"
      '';
    nix-evaluation-gc-consumers =
      pkgs.runCommand "check-nix-evaluation-gc-consumers" { nativeBuildInputs = [ pkgs.gnugrep ]; }
        ''
          export NIX_REMOTE=local
          export NIX_STATE_DIR="$TMPDIR/nix-state"
          export NIX_STORE_DIR="$TMPDIR/nix-store"
          export NIX_LOG_DIR="$TMPDIR/nix-log"
          LD_DEBUG=libs ${gcExperiment.stockCommand}/bin/nix-evaluation --version > stock.version 2> stock.loader
          LD_DEBUG=libs ${gcExperiment.candidateCommand}/bin/nix-evaluation --version > candidate.version 2> candidate.loader
          grep -F 'calling init: ${gcExperiment.stock}/lib/libgc.so.1' stock.loader
          grep -F 'calling init: ${gcExperiment.candidate}/lib/libgc.so.1' candidate.loader
          cmp stock.version candidate.version
          test "$(cat stock.version)" = 'nix (Nix) ${gcExperiment.consumer.version}'
          ${gcExperiment.stockCommand}/bin/nix-evaluation --extra-experimental-features nix-command eval --raw --expr "builtins.toString (builtins.foldl' (a: b: a + b) 0 (builtins.genList (x: x) 100000))" > stock.evaluation
          ${gcExperiment.candidateCommand}/bin/nix-evaluation --extra-experimental-features nix-command eval --raw --expr "builtins.toString (builtins.foldl' (a: b: a + b) 0 (builtins.genList (x: x) 100000))" > candidate.evaluation
          cmp stock.evaluation candidate.evaluation
          test "$(cat stock.evaluation)" = 4999950000
          touch "$out"
        '';
    optimization-control-inputs =
      assert toString recoverySystem.config.system.build.isoImage == stock.recoveryIso;
      assert inputs.nixpkgs.rev == stock.nixpkgsRevision;
      assert pkgs.lib.hasInfix "-nixos-opt-cpu-" (toString candidate);
      pkgs.runCommand "check-optimization-control-inputs" { } ''touch "$out"'';
    optimization-schema =
      assert import ./experiment/test.nix { inherit (pkgs) lib; };
      pkgs.runCommand "check-optimization-schema" { } ''touch "$out"'';
    optimization-runtime-statistics =
      pkgs.runCommand "check-optimization-runtime-statistics"
        {
          nativeBuildInputs = [
            pkgs.python3
            pkgs.ruff
          ];
        }
        ''
          cp -r ${./provenance} provenance
          cp -r ${./runners} runners
          chmod -R u+w provenance runners
          python -m py_compile provenance/*.py runners/*.py
          ruff format --check provenance runners
          ruff check provenance runners
          export PYTHONDONTWRITEBYTECODE=1
          python ${./provenance}/test_runtime.py
          python ${./runners}/test_statistics.py
          PYTHONPATH=${./provenance}:${./runners} python ${./runners}/test_zstd.py
          PYTHONPATH=${./provenance}:${./runners} python ${./runners}/test_nix_evaluation.py
          touch "$out"
        '';
  };
}
