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
    optimization-zstd-runner = pkgs.writeShellApplication {
      name = "nixos-optimization-zstd";
      runtimeInputs = [
        pkgs.python3
        pkgs.git
        pkgs.util-linux
        pkgs.systemd
        pkgs.sudo
      ];
      text = ''
        export PYTHONDONTWRITEBYTECODE=1
        export PYTHONPATH=${./provenance}:${./runners}
        exec python ${./runners}/zstd.py "$@"
      '';
    };
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
          PYTHONPATH=${./provenance}:${./runners} python ${./runners}/test_zstd.py
          touch "$out"
        '';
  };
}
