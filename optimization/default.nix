{
  pkgs,
  inputs,
  repository,
  systemConfig,
  recoverySystem,
}:
let
  stock = import ./control/stock.nix;
  model = import ./experiment/model.nix { inherit (pkgs) lib; };
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
    # Explicit experiment admission gate. Ordinary workstation applications
    # may change the desktop; measurements still require the frozen control.
    optimization-control-identity =
      assert toString systemConfig.config.system.build.toplevel == stock.normal;
      assert
        toString systemConfig.config.specialisation.persistent-root.configuration.system.build.toplevel
        == stock.persistentRoot;
      assert toString recoverySystem.config.system.build.isoImage == stock.recoveryIso;
      assert builtins.hashFile "sha256" (repository + "/flake.lock") == stock.lockSha256;
      assert inputs.nixpkgs.rev == stock.nixpkgsRevision;
      pkgs.runCommand "check-optimization-control-identity" { } ''touch "$out"'';
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
    optimization-control-inputs =
      assert toString recoverySystem.config.system.build.isoImage == stock.recoveryIso;
      assert builtins.hashFile "sha256" (repository + "/flake.lock") == stock.lockSha256;
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
          touch "$out"
        '';
  };
}
