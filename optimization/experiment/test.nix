{ lib }:
let
  model = import ./model.nix { inherit lib; };
  fixture = import ../experiments/zstd-skylake/spec.nix;
  accepts = value: (builtins.tryEval (builtins.deepSeq (model.normalizeSpec value) true)).success;
  workload = builtins.head fixture.workloads;
  compilerStage =
    comparison: profileNarHash:
    fixture
    // {
      stage = {
        kind = "gc-compiler-comparison";
        parameters = {
          inherit comparison profileNarHash;
          packageAllowList = [ "boehm-gc" ];
        };
      };
    };
in
assert accepts fixture;
assert accepts (compilerStage "thinlto" null);
assert accepts (compilerStage "pgo" "sha256-arWimsz14Zt4kBXtuwA9Brt7BVIMuNRQ92V8rEw5c+k=");
assert !(accepts (compilerStage "pgo" null));
assert !(accepts (compilerStage "pgo" "unbound-profile"));
assert !(accepts (compilerStage "thinlto" "unrelated-profile"));
assert !(accepts (compilerStage "thinlto-pgo-bolt" null));
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
