{
  schemaVersion = 2;
  id = "boehmgc-nix-evaluation-cpu-target";
  hypothesis = "CPU targeting the GC hot path reduces Nix evaluation time beyond a one-percent practical threshold.";
  physicalTarget = {
    hostname = "desktop";
    cpuVendor = "GenuineIntel";
    cpuFamily = "6";
    cpuModel = "165";
  };
  stage = {
    kind = "cpu-codegen";
    parameters = {
      march = "skylake";
      mtune = "skylake";
      packageAllowList = [ "boehm-gc" ];
    };
  };
  targets = [
    {
      id = "stock";
      kind = "package";
      attribute = "nix-evaluation-stock";
    }
    {
      id = "candidate";
      kind = "package";
      attribute = "nix-evaluation-candidate";
    }
  ];
  workloads = [
    {
      id = "repository-evaluation";
      description = "Offline evaluation of the pinned real repository and all flake outputs on one declared CPU.";
      executable = "bin/nix-evaluation";
      arguments = [
        "flake"
        "check"
        "@source@"
        "--offline"
        "--no-build"
        "--no-write-lock-file"
        "--no-eval-cache"
      ];
      corpusId = "nix-evaluation";
      cpu = 2;
      warmupRuns = 1;
      minimumSeconds = 1;
      metrics = [
        {
          id = "wallTime";
          unit = "seconds";
          direction = "lower-is-better";
        }
        {
          id = "cpuTime";
          unit = "seconds";
          direction = "lower-is-better";
        }
      ];
      sampling = {
        pilotPairs = 4;
        minimumPairs = 10;
        maximumPairs = 20;
        targetDeltaHalfWidth = 0.02;
        effectThreshold = 0.01;
        orderSeed = 20261015;
      };
    }
  ];
}
