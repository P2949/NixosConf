{ lib }:
let
  model = import ./model.nix { inherit lib; };
  fixture = import ../experiments/zstd-skylake/spec.nix;
  accepts = value: (builtins.tryEval (builtins.deepSeq (model.normalizeSpec value) true)).success;
  workload = builtins.head fixture.workloads;
in
assert accepts fixture;
assert !(accepts (fixture // { unknown = true; }));
assert !(accepts (fixture // { schemaVersion = 1; }));
assert
  !(accepts (
    fixture
    // {
      stage = {
        kind = "cpu-codegen";
        parameters = {
          march = "skylake";
          mtune = "skylake";
        };
      };
    }
  ));
assert
  !(accepts (
    fixture
    // {
      workloads = [
        (
          workload
          // {
            sampling = workload.sampling // {
              pilotPairs = 1;
            };
          }
        )
      ];
    }
  ));
assert !(accepts (fixture // { targets = fixture.targets ++ fixture.targets; }));
assert !(accepts (fixture // { workloads = [ (workload // { warmupRuns = -1; }) ]; }));
true
