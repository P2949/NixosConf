{
  pkgs,
  packages,
  repository,
}:
let
  corpus = import ../../corpora/nix-evaluation.nix {
    inherit pkgs;
    revision = "4a122b6f2898269d9c8d85a15d655f4bcb80b195";
    narHash = "sha256-zKS9aBPg3RmeFMC7aUTnrTictkBCwAlcC6f5vEXmC5E=";
  };
  metadata = pkgs.writeText "boehmgc-pgo-training-inputs.json" (
    builtins.unsafeDiscardStringContext (
      builtins.toJSON {
        schemaVersion = 1;
        kind = "boehmgc-pgo-training";
        acceptance = "TRAINING_ONLY_NOT_BENCHMARK";
        sourceRevision = repository.rev;
        sourceNarHash = repository.narHash;
        compilerVersion = pkgs.llvmPackages.clang.version;
        compiler = toString pkgs.llvmPackages.clang;
        consumer = toString packages.consumer;
        variants = builtins.mapAttrs (id: package: {
          instrumentedDerivation = package.drvPath;
          instrumentedOutput = toString package;
          command = "${packages.commands.${id}}/bin/nix-evaluation-pgo-training";
          source = toString package.src;
          compileFlags = package.NIX_CFLAGS_COMPILE;
        }) packages.instrumented;
      }
    )
  );
in
pkgs.testers.runNixOSTest {
  name = "boehmgc-pgo-training";
  nodes.machine = {
    system.extraDependencies = [ corpus ] ++ builtins.attrValues packages.commands;
    virtualisation = {
      memorySize = 8192;
      cores = 2;
      graphics = false;
      qemu.options = [ "-vga none" ];
    };
  };
  testScript = ''
    import json
    from pathlib import Path
    import shlex

    metadata = json.loads(Path("${metadata}").read_text())
    corpus = json.loads(Path("${corpus}").read_text())
    start_all()
    machine.wait_for_unit("multi-user.target")
    machine.wait_for_unit("register-nix-paths.service")
    machine.succeed("mkdir -p /tmp/pgo-training")
    for variant, artifact in metadata["variants"].items():
        with subtest(f"real repository training with {variant}"):
            directory = f"/tmp/pgo-training/{variant}"
            machine.succeed(f"mkdir -p {directory}/raw {directory}/home {directory}/cache {directory}/config {directory}/state")
            env = ["env", f"HOME={directory}/home", f"XDG_CACHE_HOME={directory}/cache",
                f"XDG_CONFIG_HOME={directory}/config", f"XDG_STATE_HOME={directory}/state",
                f"NIX_CONF_DIR={directory}/config", "NIX_REMOTE=daemon", "LD_DEBUG=libs",
                f"LLVM_PROFILE_FILE={directory}/raw/%p-%m.profraw"]
            args = [artifact["command"], "eval", "--offline", "--no-write-lock-file",
                "--no-eval-cache", "--extra-experimental-features", "nix-command flakes",
                "--raw", f"path:{corpus['source']['path']}#nixosConfigurations.desktop.config.system.build.toplevel.drvPath"]
            machine.succeed(f"{shlex.join(env + args)} > {directory}/evaluation.txt 2> {directory}/loader.txt", timeout=600)
            result = machine.succeed(f"cat {directory}/evaluation.txt").strip()
            assert result.startswith("/nix/store/") and result.endswith(".drv"), result
            loader = machine.succeed(f"cat {directory}/loader.txt")
            assert f"calling init: {artifact['instrumentedOutput']}/lib/libgc.so.1" in loader
            raw = machine.succeed(f"find {directory}/raw -type f -name '*.profraw' -size +0c").splitlines()
            assert raw, variant
            receipt = dict(metadata, variant=variant, artifact=artifact, trainingCorpus=corpus,
                trainingCommand=args, trainingEnvironment=env, evaluatedDerivation=result,
                rawProfiles={path.rsplit("/", 1)[1]: machine.succeed(f"sha256sum {shlex.quote(path)}").split()[0] for path in raw})
            machine.succeed(f"printf %s {shlex.quote(json.dumps(receipt, sort_keys=True))} > {directory}/receipt.json")
    machine.copy_from_machine("/tmp/pgo-training", "training")
    print("TRAINING_ONLY: raw profiles from the pinned real repository; independent benchmark still required")
  '';
}
