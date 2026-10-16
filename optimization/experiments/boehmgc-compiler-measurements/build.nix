{
  pkgs,
  repository,
  comparison,
  profiles ? { },
}:
let
  inherit (pkgs) lib;
  pairs = import ./comparisons.nix { inherit pkgs profiles; };
  pair = pairs.${comparison};
  artifact = value: {
    output = toString value;
    derivation = value.drvPath;
  };
  toolchain =
    package:
    let
      compiler = package.compilerExperiment.compiler or pkgs.stdenv.cc;
      linker = package.compilerExperiment.linker or pkgs.stdenv.cc.bintools;
    in
    {
      compiler = artifact compiler;
      compilerVersion = compiler.version;
      linker = artifact linker;
      linkerVersion = linker.version;
    };
  variants = { inherit (pair) stock candidate; };
  commands = lib.mapAttrs (
    _: package:
    pkgs.writeShellApplication {
      name = "nix-evaluation";
      text = ''
        unset LD_PRELOAD LD_AUDIT
        export LD_LIBRARY_PATH=${package}/lib
        exec ${pair.consumer}/bin/nix "$@"
      '';
    }
  ) variants;
  profileVariant = if comparison == "pgo" then "generic" else "skylake";
  manifest = {
    schemaVersion = 1;
    kind = "nixos-gc-compiler-comparison";
    acceptance = "PREPARATION_ONLY_NOT_PERFORMANCE";
    source = {
      revision = repository.rev;
      narHash = repository.narHash;
      lockSha256 = builtins.hashFile "sha256" (repository + "/flake.lock");
    };
    inherit comparison;
    inherit (pair) attribution collectorPolicy packageAllowList;
    consumer = artifact pair.consumer;
    libraries = lib.mapAttrs (
      id: package:
      artifact package
      // {
        inherit (package) version configureFlags makeFlags;
        source = artifact package.src // {
          narHash = package.src.outputHash;
        };
        compileFlags = package.NIX_CFLAGS_COMPILE or "";
        linkFlags = package.NIX_LDFLAGS or "";
        toolchain = toolchain package;
        command = artifact commands.${id};
        audit = if package ? audit then toString package.audit else null;
      }
    ) variants;
    profile =
      if
        builtins.elem comparison [
          "pgo"
          "cpu-pgo"
        ]
      then
        {
          inherit (profiles.${profileVariant}) profilePath profileNarHash;
          variant = profileVariant;
          mergedProfileSha256 = builtins.hashFile "sha256" (pair.candidate.pgoProfile + "/merged.profdata");
          metadataSha256 = builtins.hashFile "sha256" (pair.candidate.pgoProfile + "/profile.json");
        }
      else
        null;
  };
in
assert repository ? rev;
assert pair.stock.src == pair.candidate.src;
assert pair.stock.configureFlags == pair.candidate.configureFlags;
assert pair.stock.makeFlags == pair.candidate.makeFlags;
{
  inherit commands manifest;
  libraries = variants;
  metadata = pkgs.writeText "boehmgc-${comparison}-comparison.json" (
    builtins.unsafeDiscardStringContext (builtins.toJSON manifest) + "\n"
  );
}
