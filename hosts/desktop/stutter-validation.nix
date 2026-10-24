{
  config,
  username,
  ...
}:

let
  stateRoot = "/var/lib/stutter-validation";
  home = config.users.users.${username}.home;
  repository = "${home}/Development/stutter";
  runner = "${stateRoot}/bin/stutter-validation-runner";
  authorization = "${stateRoot}/current/authorization.json";
  services = [
    "stutter-validation-runner.service"
    "stutter-validation-resume.service"
  ];
in
{
  # The root-owned statement Stutter's installer trusts (and an unprivileged caller cannot
  # forge): the units below are declared by this host and `${stateRoot}` persists across the
  # ephemeral-root reset, so a validation campaign may reboot and resume. The contract is
  # `persistent-runner-v1`; any field mismatch makes the installer fall back to transient units.
  environment.etc."stutter-validation/persistent-runner-v1.json".text = builtins.toJSON {
    contract_version = 1;
    state_root = stateRoot;
    inherit services repository;
  };

  systemd.services.stutter-validation-runner = {
    description = "Stutter validation runner (validation infrastructure, not a product component)";
    documentation = [ "https://github.com/P2949/stutter/blob/main/docs/VALIDATION_CAMPAIGN.md" ];
    wantedBy = [ "multi-user.target" ];
    after = [ "local-fs.target" ];
    # An idle machine (no campaign installed) must not produce a failed unit, and the
    # activation of this configuration must never restart a running campaign's runner.
    unitConfig.ConditionPathExists = authorization;
    restartIfChanged = false;
    serviceConfig = {
      Type = "simple";
      ExecStart = "${runner} serve --authorization ${authorization} --state-dir ${stateRoot}/current";
      RuntimeDirectory = "stutter-validation";
      RuntimeDirectoryMode = "0755";
      StateDirectory = "stutter-validation";
      StateDirectoryMode = "0700";
      Restart = "on-failure";
      RestrictAddressFamilies = "AF_UNIX";
      PrivateTmp = true;
      ProtectHome = "read-only";
      ProtectSystem = "full";
      # Capability delegation to the profiling suites needs it; the bounding set is minimal.
      NoNewPrivileges = false;
      CapabilityBoundingSet = [
        "CAP_SETUID"
        "CAP_SETGID"
        "CAP_SETPCAP"
        "CAP_BPF"
        "CAP_PERFMON"
        "CAP_SYS_RESOURCE"
        "CAP_SYS_NICE"
        "CAP_SYS_BOOT"
        "CAP_CHOWN"
        "CAP_DAC_OVERRIDE"
        "CAP_DAC_READ_SEARCH"
      ];
      AmbientCapabilities = "";
      LockPersonality = true;
      RestrictRealtime = false;
      # The suites write their results under the checkout's .llm-runs and build offline from
      # the owner's cargo home; nothing else under the read-only home is writable.
      ReadWritePaths = [
        "-${repository}/.llm-runs"
        "-${home}/.cargo"
      ];
    };
  };

  systemd.services.stutter-validation-resume = {
    description = "Resume an authorized Stutter validation campaign after a reboot (validation only)";
    wantedBy = [ "multi-user.target" ];
    after = [
      "local-fs.target"
      "stutter-validation-runner.service"
    ];
    requires = [ "stutter-validation-runner.service" ];
    before = [ "multi-user.target" ];
    unitConfig.ConditionPathExists = authorization;
    restartIfChanged = false;
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${runner} resume --all --wait-for-runner 120";
      RemainAfterExit = false;
      # The resumed controller is detached from this oneshot: it must outlive it.
      KillMode = "process";
    };
  };
}
