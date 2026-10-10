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
      command = [
        "zstd"
        "-b1"
        "-T1"
      ];
      corpusAttribute = "silesia-corpus";
      cpu = 2;
      warmupRuns = 2;
      minimumSeconds = 1;
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
        pilotPairs = 4;
        minimumPairs = 6;
        maximumPairs = 30;
        relativePrecision = 0.02;
        effectThreshold = 0.01;
        orderSeed = 20261010;
      };
    }
  ];
}
