{
  pkgs,
  inputs,
  repository,
  systemConfig,
}:
let
  model = import ./experiment/model.nix { inherit (pkgs) lib; };
  specification = model.normalizeSpec (import ./experiment/fixture.nix);
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
    zstd-stock = pkgs.zstd;
    zstd-cpu-target = candidate;
    silesia-corpus = corpus;
    optimization-spec = pkgs.writeText "experiment-spec.json" (builtins.toJSON specification + "\n");
    optimization-build-provenance = buildManifest;
  };
  checks = {
    optimization-schema =
      assert import ./experiment/test.nix { inherit (pkgs) lib; };
      pkgs.runCommand "check-optimization-schema" { } ''touch "$out"'';
    optimization-runtime-statistics =
      pkgs.runCommand "check-optimization-runtime-statistics"
        {
          nativeBuildInputs = [ pkgs.python3 ];
        }
        ''
          export PYTHONDONTWRITEBYTECODE=1
          python ${./provenance}/test_runtime.py
          python ${./runners}/test_statistics.py
          touch "$out"
        '';
  };
}
