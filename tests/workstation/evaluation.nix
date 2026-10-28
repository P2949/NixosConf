{
  pkgs,
  pkgsUnstable,
  config,
  username,
}:

let
  homePolicy = config.home-manager.users.${username}.home.persistence."/persist";
  systemPolicy = config.environment.persistence."/persist";
  homeDirectories = map (entry: entry.directory) homePolicy.directories;
  systemDirectories = map (entry: entry.directory) systemPolicy.directories;
  gpuPolicy = builtins.readFile config.hardware.lactPolicy.source;
  seed = config.systemd.services.gpu-lact-config-seed;
  systemFiles = map (entry: entry.file) systemPolicy.files;
  homeConfig = config.home-manager.users.${username};
  runnerUnit = config.systemd.services.stutter-validation-runner;
  resumeUnit = config.systemd.services.stutter-validation-resume;
  validationMarker =
    builtins.fromJSON
      config.environment.etc."stutter-validation/persistent-runner-v1.json".text;
  sabiWrappers = builtins.filter (
    package: pkgs.lib.getName package == "codex-sabi"
  ) homeConfig.home.packages;
  sabiWrapper = builtins.head sabiWrappers;
  sabiInstaller = builtins.head (
    builtins.filter (package: pkgs.lib.getName package == "sabi-model-install") homeConfig.home.packages
  );
  sabiVerifier = builtins.head (
    builtins.filter (package: pkgs.lib.getName package == "sabi-model-verify") homeConfig.home.packages
  );
  sabiUnit = homeConfig.systemd.user.services.sabi-noema;
  sabiService = sabiUnit.Service;
  sabiSocket = homeConfig.systemd.user.sockets.sabi-noema-proxy;
  sabiProxy = homeConfig.systemd.user.services.sabi-noema-proxy;
  sabiProxyExec = builtins.head sabiProxy.Service.ExecStart;
  sabiExec = builtins.head sabiService.ExecStart;
  sabiProfile = builtins.readFile homeConfig.home.file.".codex/sabi.config.toml".source;
  sabiCatalog = builtins.head (builtins.fromJSON (
    builtins.readFile (
      builtins.head (builtins.match ".*model_catalog_json = \"([^\"]+)\".*" sabiProfile)
    )
  )).models;
  topologyValid =
    !(config.fileSystems ? "/home")
    && !(config.fileSystems ? "/var")
    && config.fileSystems."/persist".neededForBoot
    && config.boot.ephemeralBtrfsRoot.enable
    && !config.specialisation.persistent-root.configuration.boot.ephemeralBtrfsRoot.enable;
  validationKernels = config.specialisation;
  validationKernelVersions = [
    config.boot.kernelPackages.kernel.modDirVersion
    validationKernels.stutter-kernel-6-12.configuration.boot.kernelPackages.kernel.modDirVersion
    validationKernels.stutter-kernel-7-2.configuration.boot.kernelPackages.kernel.modDirVersion
  ];
  # Force toplevel evaluation (including NixOS assertions) for both boot
  # policies. Discard the string context so CI does not build either closure.
  evaluation = builtins.unsafeDiscardStringContext (
    builtins.toJSON {
      desktop = config.system.build.toplevel.drvPath;
      persistentRoot = config.specialisation.persistent-root.configuration.system.build.toplevel.drvPath;
      stutterKernel612 =
        validationKernels.stutter-kernel-6-12.configuration.system.build.toplevel.drvPath;
      stutterKernel72 = validationKernels.stutter-kernel-7-2.configuration.system.build.toplevel.drvPath;
      stateVersion = config.system.stateVersion;
    }
  );
in
assert topologyValid;
# Intentional workstation recovery authority must survive generic hardening.
assert builtins.elem username config.nix.settings.trusted-users;
assert builtins.any (
  rule:
  builtins.elem username rule.users
  && builtins.any (
    command: command.command == "ALL" && builtins.elem "NOPASSWD" command.options
  ) rule.commands
) config.security.sudo.extraRules;
# Stutter's persistent autonomous multi-kernel validation (contract persistent-runner-v1).
assert builtins.elem "/var/lib/stutter-validation" (
  map (entry: entry.directory) systemPolicy.directories
);
assert
  (builtins.head (
    builtins.filter (entry: entry.directory == "/var/lib/stutter-validation") systemPolicy.directories
  )).mode == "0700";
assert
  runnerUnit.serviceConfig.ExecStart
  == "/var/lib/stutter-validation/bin/stutter-validation-runner serve --authorization /var/lib/stutter-validation/current/authorization.json --state-dir /var/lib/stutter-validation/current";
assert
  resumeUnit.serviceConfig.ExecStart
  == "/var/lib/stutter-validation/bin/stutter-validation-runner resume --all --wait-for-runner 120";
assert builtins.elem "stutter-validation-runner.service" resumeUnit.after;
assert builtins.elem "stutter-validation-runner.service" resumeUnit.requires;
assert resumeUnit.serviceConfig.KillMode == "process";
assert validationMarker.contract_version == 1;
assert validationMarker.state_root == "/var/lib/stutter-validation";
assert
  validationMarker.services == [
    "stutter-validation-runner.service"
    "stutter-validation-resume.service"
  ];
assert validationMarker.repository == "${config.users.users.${username}.home}/Development/stutter";
assert pkgs.lib.length (pkgs.lib.unique validationKernelVersions) == 3;
assert config.hardware.amdgpu.overdrive.enable;
assert config.services.lact.enable;
assert config.services.lact.package == import ../../packages/lact { inherit (pkgsUnstable) lact; };
assert config.hardware.lactPolicy.enable;
assert config.services.lact.settings == { };
assert seed.serviceConfig.Type == "oneshot" && seed.serviceConfig.RemainAfterExit;
assert builtins.elem "lactd.service" seed.before;
assert builtins.elem "lactd.service" seed.requiredBy;
assert builtins.elem "gpu-lact-config-seed.service" config.systemd.services.lactd.requires;
assert builtins.elem config.hardware.lactPolicy.source seed.restartTriggers;
assert builtins.elem config.hardware.lactPolicy.source
  config.systemd.services.lactd.restartTriggers;
assert pkgs.lib.hasInfix "current_profile: Daily\n" gpuPolicy;
assert pkgs.lib.hasInfix "auto_switch_profiles: false\n" gpuPolicy;
assert pkgs.lib.hasInfix "  Stock:\n" gpuPolicy;
assert pkgs.lib.hasInfix "  Daily:\n" gpuPolicy;
assert pkgs.lib.hasInfix "  Gaming:\n" gpuPolicy;
assert !(builtins.elem "/etc/lact" systemDirectories);
assert config.programs.gamemode.gpuProfile.enable;
assert pkgs.lib.hasSuffix "/bin/gamemode-gpu-profile start"
  config.programs.gamemode.settings.custom.start;
assert pkgs.lib.hasSuffix "/bin/gamemode-gpu-profile end"
  config.programs.gamemode.settings.custom.end;
assert pkgs.lib.all (path: !(builtins.elem path homeDirectories)) [
  ".config"
  ".local"
  ".cache"
];
assert pkgs.lib.all (path: builtins.elem path homeDirectories) [
  "Documents"
  "Development"
  ".codex"
  ".ssh"
  ".config/mozilla/firefox"
  ".local/state/fuzzel"
];
assert
  config.home-manager.users.${username}.programs.fuzzel.settings.main.cache
  == "${config.home-manager.users.${username}.xdg.stateHome}/fuzzel/history";
assert builtins.elem "/var/lib/systemd/random-seed" systemFiles;
assert builtins.elem ".local/share/local-ai" homeDirectories;
assert !(builtins.elem ".local/share" homeDirectories);
assert pkgs.lib.hasInfix "-rocm" sabiExec && pkgs.lib.hasInfix "/bin/llama-server " sabiExec;
assert pkgs.lib.all (flag: pkgs.lib.hasInfix flag sabiExec) [
  "--host 127.0.0.1 "
  "--port 11436 "
  "--n-gpu-layers all "
  "--ctx-size 61440 "
  "--cache-ram 0 "
  "--no-cache-idle-slots "
  "--cache-type-k q4_1 "
  "--cache-type-v q4_1 "
  "--flash-attn on "
  "--fit off "
  "--parallel 1 "
  "--no-context-shift "
  "--sleep-idle-seconds 300 "
  "--jinja "
  "--chat-template-file "
  "--no-reasoning-preserve "
  "/local-ai/models/63c4e5c0012e5445cea31822a40f54f2628fb8f3/Sabi-Noema-Q3_K_M.gguf "
];
# Physical qualification found no benefit from --poll 0; retain upstream polling.
assert !(pkgs.lib.hasInfix "--poll " sabiExec);
assert builtins.elem "HIP_VISIBLE_DEVICES=0" (pkgs.lib.toList sabiService.Environment);
assert !(pkgs.lib.hasInfix "--no-cache-prompt" sabiExec);
assert sabiUnit.Unit.StopWhenUnneeded;
assert pkgs.lib.toList sabiSocket.Socket.ListenStream == [ "127.0.0.1:11435" ];
assert !sabiSocket.Socket.Accept && sabiSocket.Socket.NoDelay;
assert builtins.elem "sockets.target" sabiSocket.Install.WantedBy;
assert pkgs.lib.all
  (unit: builtins.elem unit sabiProxy.Unit.Requires && builtins.elem unit sabiProxy.Unit.After)
  [
    "sabi-noema.service"
    "sabi-noema-proxy.socket"
  ];
assert pkgs.lib.hasSuffix "/lib/systemd/systemd-socket-proxyd --exit-idle-time=300s 127.0.0.1:11436"
  sabiProxyExec;
assert sabiProxy.Service.Type == "notify";
assert pkgs.lib.hasSuffix "/bin/sabi-noema-ready" (
  builtins.head (pkgs.lib.toList sabiProxy.Service.ExecStartPre)
);
assert sabiProxy.Service.TimeoutStartSec == 250;
# Backend activation belongs to the proxy dependency, never the login target.
assert !(sabiUnit ? Install) || (sabiUnit.Install.WantedBy or [ ]) == [ ];
assert !(config.systemd.services ? sabi-noema);
assert pkgs.lib.all (port: !(builtins.elem port config.networking.firewall.allowedTCPPorts)) [
  11435
  11436
];
assert builtins.elem pkgsUnstable.codex homeConfig.home.packages;
assert homeConfig.home.file ? ".codex/sabi.config.toml";
assert !(homeConfig.home.file ? ".codex/config.toml");
assert pkgs.lib.all (line: pkgs.lib.hasInfix line sabiProfile) [
  ''model = "sabi-noema"''
  ''base_url = "http://127.0.0.1:11435/v1"''
  ''wire_api = "responses"''
  "requires_openai_auth = false"
  "model_context_window = 61440"
  "model_auto_compact_token_limit = 50000"
  ''approval_policy = "never"''
  ''sandbox_mode = "danger-full-access"''
  ''web_search = "disabled"''
  "model_catalog_json = "
];
assert sabiCatalog.context_window == 61440 && sabiCatalog.max_context_window == 61440;
assert builtins.length sabiWrappers == 1;
assert
  builtins.length (
    builtins.filter (package: pkgs.lib.getName package == "sabi-model-verify") homeConfig.home.packages
  ) == 1;
assert sabiCatalog.effective_context_window_percent == 95;
assert sabiCatalog.tool_mode == "direct";
assert
  map (level: level.effort) sabiCatalog.supported_reasoning_levels == [
    "low"
    "medium"
    "xhigh"
  ];
assert sabiCatalog.default_reasoning_level == "xhigh";
# Codex's Responses/tool wire behavior is part of the compatibility boundary.
assert pkgsUnstable.codex.version == "0.159.3";
assert config.services.journald.storage == "volatile";
pkgs.runCommand "check-desktop-evaluation"
  {
    inherit evaluation;
    nativeBuildInputs = [ pkgs.python3 ];
  }
  ''
    grep -F -- 'systemctl --user start sabi-noema-proxy.socket' ${sabiWrapper}/bin/codex-sabi
    grep -F -- 'http://127.0.0.1:11435/props' ${sabiWrapper}/bin/codex-sabi
    ! grep -F -- 'systemctl --user start sabi-noema.service' ${sabiWrapper}/bin/codex-sabi
    grep -F -- '--profile sabi' ${sabiWrapper}/bin/codex-sabi
    grep -F -- '--dangerously-bypass-approvals-and-sandbox' ${sabiWrapper}/bin/codex-sabi
    python3 - <<'PY'
    import concurrent.futures
    import hashlib
    import os
    from pathlib import Path
    import re
    import subprocess
    import sys
    import tempfile

    root = Path(tempfile.mkdtemp())
    dest = root / "model.gguf"
    calls = root / "downloads"
    payload = b"trusted fixture bytes\n"
    corrupt = b"X" * len(payload)
    fixture = root / "fixture"
    fixture.write_bytes(payload)
    fake_curl = root / "curl"
    fake_curl.write_text("#!" + sys.executable + "\n" + """
    import os, pathlib, sys, time
    args = sys.argv[1:]
    dest = pathlib.Path(args[args.index("--output") + 1])
    with open(os.environ["DOWNLOAD_CALLS"], "a") as calls:
        calls.write("download\\n")
    time.sleep(0.1)
    data = pathlib.Path(os.environ["DOWNLOAD_FIXTURE"]).read_bytes()
    if os.environ.get("CORRUPT_DOWNLOAD"):
        data = b"X" * len(data)
    if "--continue-at" in args and dest.exists():
        data = dest.read_bytes() + data
    dest.write_bytes(data)
    """)
    fake_curl.chmod(0o700)
    # Inspect unit metadata without building the inference engine for this fixture.
    real_path = re.search(r"--model (\S+)", ${builtins.toJSON (builtins.unsafeDiscardStringContext sabiExec)}).group(1)
    commands = {}
    for name, original in [
        ("install", "${sabiInstaller}/bin/sabi-model-install"),
        ("verify", "${sabiVerifier}/bin/sabi-model-verify"),
    ]:
        script = Path(original).read_text()
        for old, new in [
            (real_path, str(dest)),
            ("13301443488", str(len(payload))),
            ("7fcf50e0cc26d31655baa81a1086638b7fd5797ee7ff9eef764f3cfd02cf3e1e", hashlib.sha256(payload).hexdigest()),
        ]:
            assert old in script, (name, old)
            script = script.replace(old, new)
        script = script.replace("curl --fail", str(fake_curl) + " --fail")
        commands[name] = root / name
        commands[name].write_text(script)
        commands[name].chmod(0o700)
    env = dict(os.environ, DOWNLOAD_CALLS=str(calls), DOWNLOAD_FIXTURE=str(fixture))

    def run(name, success=True, **extra):
        result = subprocess.run([str(commands[name])], env=dict(env, **extra), capture_output=True, text=True)
        assert (result.returncode == 0) == success, (name, result.stdout, result.stderr)

    def downloads():
        return len(calls.read_text().splitlines()) if calls.exists() else 0

    def reset():
        for path in root.glob("model.gguf*"):
            path.unlink()
        calls.unlink(missing_ok=True)

    run("verify", False)
    run("install")
    assert dest.read_bytes() == payload and downloads() == 1
    run("verify")
    orphan = root / "model.gguf.quarantine.interrupted"
    orphan.write_bytes(corrupt)
    run("install")
    assert downloads() == 1  # A valid final file is never downloaded again.
    assert not orphan.exists()  # Finish cleanup if interrupted after atomic publication.
    for bad in (b"short", corrupt):
        reset()
        dest.write_bytes(bad)
        run("verify", False)
        run("install")
        assert dest.read_bytes() == payload and downloads() == 1
        receipts = list(root.glob("model.gguf.integrity-failure.*"))
        assert len(receipts) == 1 and receipts[0].stat().st_mode & 0o777 == 0o600
        receipt = receipts[0].read_text()
        assert "time=" in receipt and "size=" + str(len(bad)) in receipt
        assert "sha256=" + hashlib.sha256(bad).hexdigest() in receipt
        assert not list(root.glob("model.gguf.quarantine.*"))
    reset()
    dest.with_suffix(".gguf.part").write_bytes(corrupt)
    run("install")
    assert dest.read_bytes() == payload and downloads() == 2
    reset()
    dest.write_bytes(corrupt)
    run("install", False, CORRUPT_DOWNLOAD="1")
    assert not dest.exists() and downloads() == 2
    assert list(root.glob("model.gguf.quarantine.*"))
    assert list(root.glob("model.gguf.integrity-failure.*"))
    run("install")
    assert dest.read_bytes() == payload and not list(root.glob("model.gguf.quarantine.*"))
    reset()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: run("install"), range(2)))
    assert dest.read_bytes() == payload and downloads() == 1
    print("Model integrity: missing, valid, size/hash corruption, resumed/clean failure, recovery and concurrent installation passed")
    PY
    printf '%s\n' "$evaluation" > "$out"
  ''
