{ pkgs }:
let
  # Preserve the GC policy used by Nix's dependency scope, including the larger
  # mark stack. CPU code generation is the only candidate variable.
  stock = pkgs.boehmgc.override {
    enableLargeConfig = true;
    initialMarkStackSize = 1048576;
  };
  candidate = import ../../stages/cpu-codegen.nix { inherit (pkgs) lib; } {
    package = stock;
    march = "skylake";
    mtune = "skylake";
    packageAllowList = [ "boehm-gc" ];
  };
  consumer = pkgs.nixVersions.nix_2_34;
  evaluationCommand =
    gc:
    pkgs.writeShellApplication {
      name = "nix-evaluation";
      text = ''
        unset LD_PRELOAD LD_AUDIT
        export LD_LIBRARY_PATH=${gc}/lib
        exec ${consumer}/bin/nix "$@"
      '';
    };
in
{
  inherit stock candidate consumer;
  stockCommand = evaluationCommand stock;
  candidateCommand = evaluationCommand candidate;
}
