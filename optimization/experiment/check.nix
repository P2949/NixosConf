{
  pkgs,
  lib,
}:

let
  model = import ./model.nix {
    inherit lib;
  };

  validSpec = model.normalizeSpec {
    id = "cpu-codegen-test";

    hypothesis = "CPU-specific code generation improves performance without regressions.";

    stage = {
      kind = "cpu-codegen";

      parameters = {
        architecture = "test";
      };
    };

    targets = [
      {
        id = "system";
        kind = "system";
        attribute = "nixosConfigurations.desktop.config.system.build.toplevel";
      }
    ];

    workloads = [
      {
        id = "example-throughput";
        description = "Synthetic throughput workload used to test the schema.";

        command = [
          "example-benchmark"
          "--iterations"
          "100"
        ];

        warmupRuns = 2;
        measurementRuns = 10;

        metrics = [
          {
            id = "wall-time";
            unit = "seconds";
            direction = "lower-is-better";
          }

          {
            id = "throughput";
            unit = "operations-per-second";
            direction = "higher-is-better";
          }
        ];
      }
    ];
  };

  invalidStage = builtins.tryEval (
    builtins.deepSeq (model.normalizeSpec {
      id = "invalid-stage";
      hypothesis = "This fixture must fail validation.";

      stage = {
        kind = "not-a-real-stage";
      };

      targets = [
        {
          id = "system";
          kind = "system";
          attribute = "nixosConfigurations.desktop.config.system.build.toplevel";
        }
      ];

      workloads = [
        {
          id = "test";
          description = "Invalid-stage validation fixture.";
          command = [ "true" ];

          metrics = [
            {
              id = "wall-time";
              unit = "seconds";
              direction = "lower-is-better";
            }
          ];
        }
      ];
    }) true
  );

  invalidDirection = builtins.tryEval (
    builtins.deepSeq (model.normalizeSpec {
      id = "invalid-direction";
      hypothesis = "This fixture must fail validation.";

      stage = {
        kind = "cpu-codegen";
      };

      targets = [
        {
          id = "system";
          kind = "system";
          attribute = "nixosConfigurations.desktop.config.system.build.toplevel";
        }
      ];

      workloads = [
        {
          id = "test";
          description = "Invalid metric direction fixture.";
          command = [ "true" ];

          metrics = [
            {
              id = "wall-time";
              unit = "seconds";
              direction = "sideways";
            }
          ];
        }
      ];
    }) true
  );

  specJson = builtins.toJSON validSpec;
in
assert !invalidStage.success;
assert !invalidDirection.success;
pkgs.runCommand "check-optimization-experiment-model"
  {
    nativeBuildInputs = [
      pkgs.jq
    ];

    inherit specJson;
  }
  ''
    printf '%s\n' "$specJson" > spec.json

    jq -e '
      .schemaVersion == 1
      and .kind == "nixos-optimization-experiment-spec"

      and .id == "cpu-codegen-test"
      and .stage.kind == "cpu-codegen"

      and (.targets | length) == 1
      and .targets[0].kind == "system"

      and (.workloads | length) == 1
      and .workloads[0].warmupRuns == 2
      and .workloads[0].measurementRuns == 10

      and (.workloads[0].command | type) == "array"

      and .workloads[0].metrics[0].direction == "lower-is-better"
      and .workloads[0].metrics[1].direction == "higher-is-better"
    ' spec.json >/dev/null

    cp spec.json "$out"
  ''
