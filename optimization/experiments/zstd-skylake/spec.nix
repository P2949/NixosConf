{
  schemaVersion = 2;
  id = "zstd-cpu-target";
  hypothesis = "Package-scoped CPU targeting improves throughput beyond measured noise.";
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
      packageAllowList = [ "zstd" ];
    };
  };
  targets = [
    {
      id = "stock";
      kind = "package";
      attribute = "zstd-stock";
    }
    {
      id = "candidate";
      kind = "package";
      attribute = "zstd-cpu-target";
    }
  ];
  workloads = [
    {
      id = "level-1";
      description = "Single-thread Silesia compression and decompression.";
      executable = "bin/zstd";
      arguments = [
        "-b1"
        "-T1"
      ];
      corpusId = "silesia";
      cpu = 2;
      warmupRuns = 2;
      minimumSeconds = 3;
      metrics = [
        {
          id = "compression";
          unit = "MB/s";
          direction = "higher-is-better";
        }
        {
          id = "decompression";
          unit = "MB/s";
          direction = "higher-is-better";
        }
      ];
      sampling = {
        pilotPairs = 6;
        minimumPairs = 10;
        maximumPairs = 30;
        targetDeltaHalfWidth = 0.02;
        effectThreshold = 0.01;
        orderSeed = 20261010;
      };
    }
  ];
}
