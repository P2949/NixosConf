{
  pkgs,
  packages,
  corpus,
}:
pkgs.testers.runNixOSTest {
  name = "boehmgc-thinlto-functional";
  nodes.machine = {
    system.extraDependencies = [
      corpus
    ]
    ++ builtins.attrValues packages.allVariants
    ++ builtins.attrValues packages.commands;
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

    matrix = json.loads(Path("${packages.manifest}").read_text())
    corpus = json.loads(Path("${corpus}").read_text())
    assert matrix["acceptance"] == "FUNCTIONAL_ONLY_NOT_PERFORMANCE"
    assert matrix["sourceRevision"]
    source = corpus["source"]["path"]
    start_all()
    machine.wait_for_unit("multi-user.target")
    machine.wait_for_unit("register-nix-paths.service")
    machine.succeed("mkdir -p /tmp/gc-lto-functional")
    for variant, artifact in matrix["variants"].items():
        with subtest(f"actual Nix consumer with {variant}"):
            directory = f"/tmp/gc-lto-functional/{variant}"
            machine.succeed(f"mkdir -p {directory}/home {directory}/cache {directory}/config {directory}/state")
            env = shlex.join(["env", f"HOME={directory}/home",
                f"XDG_CACHE_HOME={directory}/cache", f"XDG_CONFIG_HOME={directory}/config",
                f"XDG_STATE_HOME={directory}/state", f"NIX_CONF_DIR={directory}/config", "NIX_REMOTE=daemon"])
            command = artifact["command"] + "/bin/nix-evaluation"
            version = machine.succeed(f"{env} {shlex.quote(command)} --version").strip()
            assert version == "nix (Nix) ${packages.consumer.version}", version
            args = [command, "eval", "--offline", "--no-write-lock-file", "--no-eval-cache",
                "--extra-experimental-features", "nix-command flakes", "--json",
                f"path:{source}#nixosConfigurations.desktop.config.boot.initrd.kernelModules"]
            machine.succeed(f"{env} LD_DEBUG=libs {shlex.join(args)} > {directory}/modules.json 2> {directory}/loader.txt", timeout=180)
            modules = json.loads(machine.succeed(f"cat {directory}/modules.json"))
            assert modules == ["btrfs", "dm_mod"], (variant, modules)
            loader = machine.succeed(f"cat {directory}/loader.txt")
            assert f"calling init: {artifact['output']}/lib/libgc.so.1" in loader, variant
    machine.copy_from_machine("/tmp/gc-lto-functional", "functional")
    print("FUNCTIONAL_ONLY: all six variants evaluated the pinned real repository offline; no performance verdict")
  '';
}
