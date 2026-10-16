{
  pkgs,
  profiles,
}:
let
  packages = import ./packages.nix { inherit pkgs; };
  optimized = builtins.mapAttrs (
    variant: identity:
    import ./optimized.nix {
      inherit pkgs variant;
      inherit (identity) profilePath profileNarHash;
    }
  ) profiles;
  variants = {
    generic-control = packages.controls.generic;
    skylake-control = packages.controls.skylake;
    generic-pgo = optimized.generic;
    skylake-pgo = optimized.skylake;
  };
  corpus = import ../../corpora/nix-evaluation.nix { inherit pkgs; };
  metadata = pkgs.writeText "boehmgc-pgo-functional.json" (
    builtins.unsafeDiscardStringContext (builtins.toJSON (builtins.mapAttrs (_: toString) variants))
  );
in
assert
  builtins.attrNames profiles == [
    "generic"
    "skylake"
  ];
pkgs.testers.runNixOSTest {
  name = "boehmgc-pgo-functional";
  nodes.machine = {
    system.extraDependencies = [
      corpus
      packages.consumer
    ]
    ++ builtins.attrValues variants;
    virtualisation = {
      memorySize = 4096;
      cores = 2;
      graphics = false;
      qemu.options = [ "-vga none" ];
    };
  };
  testScript = ''
    import json
    from pathlib import Path
    import shlex

    variants = json.loads(Path("${metadata}").read_text())
    corpus = json.loads(Path("${corpus}").read_text())
    start_all()
    machine.wait_for_unit("multi-user.target")
    machine.wait_for_unit("register-nix-paths.service")
    for variant, output in variants.items():
        with subtest(f"unchanged consumer with {variant}"):
            directory = f"/tmp/pgo-functional/{variant}"
            machine.succeed(f"mkdir -p {directory}/home {directory}/cache {directory}/config {directory}/state {directory}/raw")
            env = ["env", "-u", "LD_PRELOAD", "-u", "LD_AUDIT", f"HOME={directory}/home",
                f"XDG_CACHE_HOME={directory}/cache", f"XDG_CONFIG_HOME={directory}/config",
                f"XDG_STATE_HOME={directory}/state", f"NIX_CONF_DIR={directory}/config",
                "NIX_REMOTE=daemon", "LD_DEBUG=libs", f"LD_LIBRARY_PATH={output}/lib",
                f"LLVM_PROFILE_FILE={directory}/raw/%p-%m.profraw"]
            args = ["${packages.consumer}/bin/nix", "eval", "--offline", "--no-write-lock-file",
                "--no-eval-cache", "--extra-experimental-features", "nix-command flakes", "--json",
                f"path:{corpus['source']['path']}#nixosConfigurations.desktop.config.boot.initrd.kernelModules"]
            machine.succeed(f"{shlex.join(env + args)} > {directory}/evaluation.json 2> {directory}/loader.txt", timeout=180)
            assert json.loads(machine.succeed(f"cat {directory}/evaluation.json")) == ["btrfs", "dm_mod"]
            assert f"calling init: {output}/lib/libgc.so.1" in machine.succeed(f"cat {directory}/loader.txt")
            assert not machine.succeed(f"find {directory}/raw -type f").strip(), variant
    machine.copy_from_machine("/tmp/pgo-functional", "functional")
    print("FUNCTIONAL_ONLY: matched control/PGO consumer checks; no performance verdict")
  '';
}
