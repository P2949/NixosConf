{
  pkgs,
  inputs,
  repository,
  systemConfig,
  specification,
  corpus,
  packages,
}:
let
  artifact = value: {
    output = toString value;
    derivation = value.drvPath;
  };
  base = import ../../provenance/build.nix {
    inherit
      pkgs
      inputs
      repository
      systemConfig
      specification
      corpus
      ;
    targets = {
      stock = packages.stockCommand;
      candidate = packages.candidateCommand;
    };
  };
  gc =
    package:
    artifact package
    // {
      inherit (package) version configureFlags makeFlags;
      compileFlags = package.NIX_CFLAGS_COMPILE or "";
      source = artifact package.src;
    };
  manifest = base.manifest // {
    kind = "nixos-nix-evaluation-build";
    workloadCorpus = artifact corpus // {
      id = "nix-evaluation";
      flakeAttribute = "nix-evaluation-corpus";
    };
    consumer = artifact packages.consumer // {
      executable = "bin/nix";
      inherit (packages.consumer) version;
    };
    libraries = {
      stock = gc packages.stock;
      candidate = gc packages.candidate;
    };
    collectorPolicy = {
      enableLargeConfig = true;
      initialMarkStackSize = 1048576;
    };
  };
in
pkgs.writeText "nix-evaluation-build-provenance.json" (
  builtins.unsafeDiscardStringContext (builtins.toJSON manifest) + "\n"
)
