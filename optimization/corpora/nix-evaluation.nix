{ pkgs }:
let
  source = builtins.fetchTree {
    type = "github";
    owner = "P2949";
    repo = "NixosConf";
    rev = "658c02f637f488bf02cd6907b51718b52e133f54";
    narHash = "sha256-PGKO4Qb7PPDRcZv0SATXhKDNp9ZePk71dxgHGEBy0Kc=";
  };
  lock = builtins.fromJSON (builtins.readFile (source.outPath + "/flake.lock"));
  lockedNodes = pkgs.lib.filterAttrs (_: node: node ? locked) lock.nodes;
  inputs = builtins.mapAttrs (
    _: node:
    assert node.locked ? narHash;
    let
      tree = builtins.fetchTree node.locked;
    in
    {
      path = tree.outPath;
      inherit (node.locked) narHash;
      revision = node.locked.rev or null;
    }
  ) lockedNodes;
  manifest = {
    schemaVersion = 1;
    kind = "nixos-nix-evaluation-corpus";
    source = {
      path = source.outPath;
      inherit (source) rev narHash;
      lockSha256 = builtins.hashFile "sha256" (source.outPath + "/flake.lock");
    };
    inherit inputs;
  };
in
# String contexts retain every locked source as a store reference. The runner
# must verify these NAR identities and evaluate offline with fresh private state.
pkgs.writeText "nix-evaluation-corpus.json" (builtins.toJSON manifest + "\n")
