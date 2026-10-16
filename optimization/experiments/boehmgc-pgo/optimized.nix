{
  pkgs,
  variant,
  profilePath,
  profileNarHash,
}:
let
  packages = import ./packages.nix { inherit pkgs; };
  # Copy and verify the entire profile artifact by content, including receipts.
  # A changed profile necessarily changes this input and the optimized drv.
  profile = builtins.path {
    path = builtins.storePath profilePath;
    sha256 = profileNarHash;
    name = "boehmgc-pgo-profile";
  };
  metadata = builtins.fromJSON (builtins.readFile (profile + "/profile.json"));
  instrumented = packages.instrumented.${variant};
  control = packages.controls.${variant};
in
assert builtins.elem variant [
  "generic"
  "skylake"
];
assert metadata.kind == "boehmgc-pgo-merged-profile";
assert metadata.acceptance == "TRAINING_ONLY_NOT_BENCHMARK";
assert metadata.training.variant == variant;
assert metadata.training.artifact.instrumentedDerivation == instrumented.drvPath;
assert metadata.training.artifact.instrumentedOutput == toString instrumented;
assert metadata.training.artifact.source == toString control.src;
assert metadata.training.artifact.compileFlags == instrumented.NIX_CFLAGS_COMPILE;
assert metadata.training.compiler == toString control.compilerExperiment.compiler;
assert metadata.training.compilerDerivation == control.compilerExperiment.compiler.drvPath;
assert metadata.training.linker == toString control.compilerExperiment.linker;
assert metadata.training.linkerDerivation == control.compilerExperiment.linker.drvPath;
assert metadata.training.consumerDerivation == packages.consumer.drvPath;
assert metadata.mergedProfileSha256 == builtins.hashFile "sha256" (profile + "/merged.profdata");
control.overrideAttrs (old: {
  name = "nixos-opt-pgo-boehm-gc-${variant}-${old.version}";
  NIX_CFLAGS_COMPILE =
    (old.NIX_CFLAGS_COMPILE or "")
    + " -fprofile-instr-use=${profile}/merged.profdata"
    # Configure probes and upstream test programs are intentionally untrained.
    + " -Werror=profile-instr-out-of-date";
  postInstall = (old.postInstall or "") + ''
    ${pkgs.llvmPackages.llvm}/bin/llvm-nm --defined-only "$out/lib/libgc.so" > "$audit/profile-consumption-symbols.txt"
    if grep -q __llvm_profile_write_file "$audit/profile-consumption-symbols.txt"; then
      echo 'Optimized library still contains profile instrumentation' >&2
      exit 1
    fi
    cp ${profile}/profile.json "$audit/profile.json"
  '';
  passthru = (old.passthru or { }) // {
    pgoProfile = profile;
    inherit profileNarHash;
  };
})
