{
  pkgs,
  training,
  variant,
}:
assert builtins.elem variant [
  "generic"
  "skylake"
];
pkgs.runCommand "boehmgc-pgo-${variant}-profile"
  {
    nativeBuildInputs = [ pkgs.python3 ];
    trainingDirectory = "${training}/training/pgo-training/${variant}";
    profileTool = "${pkgs.llvmPackages.llvm}/bin/llvm-profdata";
    inherit variant;
  }
  ''
    python ${./merge.py}
  ''
