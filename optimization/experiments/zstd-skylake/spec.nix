{
  pkgs,
  lib,
  corpus,
}:

let
  model = import ../../experiment/model.nix {
    inherit lib;
  };

  spec = model.normalizeSpec {
    id = "zstd-skylake";

    hypothesis =
      "Building zstd with -march=skylake -mtune=skylake improves single-thread "
      + "compression and decompression throughput on the target system.";

    stage = {
      kind = "cpu-codegen";

      parameters = {
        march = "skylake";
        mtune = "skylake";
      };
    };

    targets = [
      {
        id = "zstd-stock";
        kind = "package";
        attribute = "nixosConfigurations.desktop.pkgs.zstd";
      }

      {
        id = "zstd-skylake";
        kind = "package";
        attribute = "packages.x86_64-linux.optimization-zstd-skylake";
      }
    ];

    workloads = [
      {
        id = "level-1";
        description = "Single-thread zstd level 1 compression and decompression.";

        command = [
          "zstd"
          "-b1"
          "-T1"
          "-i3"
          "${corpus}/silesia"
        ];

        warmupRuns = 2;
        measurementRuns = 10;

        metrics = [
          {
            id = "compression-throughput";
            unit = "MB/s";
            direction = "higher-is-better";
          }

          {
            id = "decompression-throughput";
            unit = "MB/s";
            direction = "higher-is-better";
          }
        ];
      }

      {
        id = "level-3";
        description = "Single-thread zstd level 3 compression and decompression.";

        command = [
          "zstd"
          "-b3"
          "-T1"
          "-i3"
          "${corpus}/silesia"
        ];

        warmupRuns = 2;
        measurementRuns = 10;

        metrics = [
          {
            id = "compression-throughput";
            unit = "MB/s";
            direction = "higher-is-better";
          }

          {
            id = "decompression-throughput";
            unit = "MB/s";
            direction = "higher-is-better";
          }
        ];
      }
    ];
  };
in
pkgs.writeText "zstd-skylake-experiment.json" (builtins.toJSON spec + "\n")
