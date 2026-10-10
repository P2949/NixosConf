{
  pkgs,
  inputs,
  repository,
  systemConfig,
  specification,
  targets,
  corpus,
}:
let
  identity = input: {
    revision = input.rev or null;
    narHash = input.narHash or null;
  };
  artifact = value: {
    output = toString value;
    derivation = value.drvPath;
  };
  manifest = {
    schemaVersion = 1;
    kind = "nixos-experiment-build";
    qualificationBaseline = import ../control/baseline.nix;
    source = {
      revision = repository.rev or (repository.dirtyRev or null);
      narHash = repository.narHash or null;
      dirty = !(repository ? rev);
      lockSha256 = builtins.hashFile "sha256" (repository + "/flake.lock");
    };
    workingStock = import ../control/stock.nix;
    evaluatedSystem = artifact systemConfig.config.system.build.toplevel;
    inputs = builtins.mapAttrs (_: identity) (pkgs.lib.filterAttrs (name: _: name != "self") inputs);
    toolchain = {
      compiler = artifact pkgs.stdenv.cc;
      compilerImplementation = artifact pkgs.stdenv.cc.cc;
      binutils = artifact pkgs.stdenv.cc.bintools;
      compilerVersion = pkgs.stdenv.cc.cc.version;
    };
    kernel = artifact systemConfig.config.boot.kernelPackages.kernel;
    inherit (specification) stage;
    packages = builtins.mapAttrs (_: artifact) targets;
    workloadCorpus = artifact corpus;
  };
in
# This records derivation/output identities, without realizing every referenced
# system/compiler/source closure merely to serialize the manifest. The runner
# must independently verify its measured binaries and corpus exist and hash them.
pkgs.writeText "experiment-build-provenance.json" (
  builtins.unsafeDiscardStringContext (builtins.toJSON manifest) + "\n"
)
