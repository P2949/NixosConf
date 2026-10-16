{
  pkgs,
  inputs,
  repository,
  systemConfig,
  comparison,
  targetAttributes,
  profiles ? { },
}:
let
  prepared = import ./build.nix {
    inherit
      pkgs
      repository
      comparison
      profiles
      ;
  };
  corpus = import ../../corpora/nix-evaluation.nix { inherit pkgs; };
  model = import ../../experiment/model.nix { inherit (pkgs) lib; };
  template = import ../boehmgc-nix-evaluation/spec.nix;
  specification = model.normalizeSpec (
    template
    // {
      id = "boehmgc-${comparison}";
      hypothesis = "The declared ${comparison} change reduces real Nix evaluation time beyond a one-percent practical threshold.";
      stage = {
        kind = "gc-compiler-comparison";
        parameters = {
          inherit comparison;
          packageAllowList = [ "boehm-gc" ];
          profileNarHash =
            if prepared.manifest.profile == null then null else prepared.manifest.profile.profileNarHash;
        };
      };
      targets =
        map
          (id: {
            inherit id;
            kind = "package";
            attribute = targetAttributes.${id};
          })
          [
            "stock"
            "candidate"
          ];
    }
  );
  base = import ../../provenance/build.nix {
    inherit
      pkgs
      inputs
      repository
      systemConfig
      specification
      corpus
      ;
    targets = prepared.commands;
  };
  manifest = (builtins.removeAttrs base.manifest [ "toolchain" ]) // {
    kind = "nixos-nix-evaluation-build";
    compilerComparison = prepared.manifest;
    inherit (prepared.manifest) libraries collectorPolicy;
    consumer = prepared.manifest.consumer // {
      executable = "bin/nix";
    };
    workloadCorpus = {
      output = toString corpus;
      derivation = corpus.drvPath;
      id = "nix-evaluation";
      flakeAttribute = "nix-evaluation-corpus";
    };
    toolchains = builtins.mapAttrs (_: library: library.toolchain) prepared.manifest.libraries;
  };
in
assert
  builtins.attrNames targetAttributes == [
    "candidate"
    "stock"
  ];
{
  inherit specification manifest;
  inherit (prepared) commands libraries;
  spec = pkgs.writeText "boehmgc-${comparison}-specification.json" (
    builtins.toJSON specification + "\n"
  );
  build = pkgs.writeText "boehmgc-${comparison}-build-provenance.json" (
    builtins.unsafeDiscardStringContext (builtins.toJSON manifest) + "\n"
  );
}
