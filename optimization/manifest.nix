{
  pkgs,
  inputs,
  repository,
  systemConfig,
  baseline,
}:

let
  inputIdentity = input: {
    revision = input.rev or null;
    narHash = input.narHash or null;
    lastModified = input.lastModified or null;
  };

  inherit (systemConfig) config;
  toplevel = config.system.build.toplevel;
  kernel = config.boot.kernelPackages.kernel;
  stdenvCc = pkgs.stdenv.cc.cc;

  manifest = {
    schemaVersion = 1;
    kind = "nixos-optimization-system-manifest";

    inherit baseline;

    repository = {
      revision = repository.rev or (repository.dirtyRev or null);

      narHash = repository.narHash or null;
    };

    host = {
      name = config.networking.hostName;
      system = pkgs.stdenv.hostPlatform.system;
      stateVersion = config.system.stateVersion;
    };

    currentSystem = {
      storePath = toString toplevel;
      derivationPath = toplevel.drvPath;
    };

    kernel = {
      inherit (kernel) version;
      storePath = toString kernel;
    };

    inputs = {
      nixpkgs = inputIdentity inputs.nixpkgs;
      nixpkgsUnstable = inputIdentity inputs.nixpkgs-unstable;
      homeManager = inputIdentity inputs.home-manager;
      disko = inputIdentity inputs.disko;
      liquidctlPr886 = inputIdentity inputs.liquidctl-pr886;
    };

    toolchain = {
      stdenv = pkgs.stdenv.name;

      stdenvCompiler = {
        name = stdenvCc.pname or stdenvCc.name;

        version = stdenvCc.version or null;
      };

      gcc = pkgs.gcc.version;
      clang = pkgs.clang.version;
      lld = pkgs.lld.version;
      binutils = pkgs.binutils.version;
      glibc = pkgs.glibc.version;
      nix = pkgs.nix.version;
    };
  };
in
pkgs.writeText "optimization-system-manifest.json" (builtins.toJSON manifest + "\n")
