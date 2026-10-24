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
  sabiUnit = homeConfig.systemd.user.services.sabi-noema;
  sabiService = sabiUnit.Service;
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
  "--port 11435 "
  "--n-gpu-layers all "
  "--ctx-size 61440 "
  "--cache-ram 8192 "
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
# Started only by codex-sabi, never at login.
assert !(sabiUnit ? Install) || (sabiUnit.Install.WantedBy or [ ]) == [ ];
assert !(config.systemd.services ? sabi-noema);
assert !(builtins.elem 11435 config.networking.firewall.allowedTCPPorts);
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
pkgs.runCommand "check-desktop-evaluation" { inherit evaluation; } ''
  grep -F -- '--profile sabi' ${sabiWrapper}/bin/codex-sabi
  grep -F -- '--dangerously-bypass-approvals-and-sandbox' ${sabiWrapper}/bin/codex-sabi
  printf '%s\n' "$evaluation" > "$out"
''
