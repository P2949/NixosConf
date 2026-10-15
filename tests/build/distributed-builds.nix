{ pkgs }:
let
  physicalGuard = pkgs.writeText "reject-virtual-benchmark.py" ''
    import importlib.util
    import os
    from pathlib import Path
    import socket
    import subprocess

    spec = importlib.util.spec_from_file_location("runtime", "${../../optimization/provenance/runtime.py}")
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    identity = {}
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        key, separator, value = line.partition(":")
        if separator:
            identity.setdefault(key.strip(), value.strip())
    control = os.path.realpath("/run/current-system")
    target = {
        "hostname": socket.gethostname(),
        "cpuVendor": identity["vendor_id"],
        "cpuFamily": identity["cpu family"],
        "cpuModel": identity["model"],
    }
    virtualization = subprocess.check_output(["systemd-detect-virt"], text=True).strip()
    assert virtualization != "none"
    snapshot = {
        "systems": {"current": control, "booted": control},
        "host": {"value": target["hostname"]},
        "cpu": {"identity": identity},
        "virtualization": virtualization,
    }
    try:
        runtime.validate_control(snapshot, control, target, {"virtualization": "none"})
    except ValueError as error:
        assert str(error) == "benchmark target is not physical", error
    else:
        raise AssertionError("benchmark admission accepted a VM")
    print("physical benchmark guard rejected " + virtualization)
  '';
  proof = pkgs.writeText "distributed-proof.nix" ''
    { mode }:
    let busybox = builtins.storePath "${pkgs.busybox}";
    in
    builtins.derivation {
      name = "distributed-proof-''${mode}";
      system = "${pkgs.stdenv.hostPlatform.system}";
      builder = "''${busybox}/bin/sh";
      args = [ "-c" "''${busybox}/bin/cat /run/build-proof-identity > $out" ];
      allowSubstitutes = false;
      preferLocalBuild = false;
      requiredSystemFeatures = if mode == "feature" then [ "remote-proof" ]
        else if mode == "kvm" then [ "kvm" ] else [];
    }
  '';
in
pkgs.testers.runNixOSTest {
  name = "distributed-builds";
  defaults = {
    virtualisation = {
      writableStore = true;
      additionalPaths = [ pkgs.busybox ];
      graphics = false;
    };
    nix.settings = {
      substituters = [ ];
      system-features = [ ];
    };
    environment.etc."distributed-proof.nix".source = proof;
  };
  nodes = {
    coordinator = {
      environment.systemPackages = [ pkgs.python3 ];
      nix.distributedBuilds = true;
      nix.settings = {
        max-jobs = 0;
        builders-use-substitutes = false;
      };
      nix.buildMachines = [
        {
          hostName = "builder";
          system = pkgs.stdenv.hostPlatform.system;
          protocol = "ssh-ng";
          sshUser = "root";
          sshKey = "/root/.ssh/build-proof";
          maxJobs = 1;
          supportedFeatures = [
            "big-parallel"
            "remote-proof"
          ];
        }
      ];
    };
    builder = { lib, ... }: {
      services.openssh = {
        enable = true;
        settings = {
          PasswordAuthentication = false;
          KbdInteractiveAuthentication = false;
          PermitRootLogin = "prohibit-password";
        };
      };
      nix.settings = {
        sandbox = true;
        system-features = lib.mkForce [
          "big-parallel"
          "remote-proof"
        ];
        extra-sandbox-paths = [ "/run/build-proof-identity" ];
      };
    };
  };
  testScript = ''
    import shlex

    start_all()
    coordinator.wait_for_unit("multi-user.target")
    coordinator.succeed("python3 ${physicalGuard}")
    builder.wait_for_unit("sshd.service")
    coordinator.succeed('mkdir -m 700 -p /root/.ssh; ssh-keygen -t ed25519 -N "" -f /root/.ssh/build-proof')
    public_key = coordinator.succeed("cat /root/.ssh/build-proof.pub").strip()
    builder.succeed("mkdir -m 700 -p /root/.ssh; printf '%s\\n' " + shlex.quote(public_key) + " > /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys")
    host_key = builder.succeed("cat /etc/ssh/ssh_host_ed25519_key.pub").strip()
    coordinator.succeed("printf '%s\\n' " + shlex.quote("builder " + host_key) + " > /root/.ssh/known_hosts")
    builder.succeed("hostname > /run/build-proof-identity")
    coordinator.succeed("test ! -e /run/build-proof-identity")

    for mode in ["basic", "feature"]:
        with subtest("remote build and transfer: " + mode):
            expression = "/etc/distributed-proof.nix --argstr mode " + mode
            output = coordinator.succeed("nix-instantiate --eval --strict " + expression + " -A outPath").strip().strip('"')
            for node in [coordinator, builder]:
                node.fail("nix-store --check-validity " + output)
            status, diagnostic = coordinator.execute("nix-build " + expression + " --no-out-link 2>&1")
            assert status == 0, diagnostic
            for node in [coordinator, builder]:
                node.succeed("nix-store --check-validity " + output)
                assert node.succeed("cat " + output).strip() == "builder"
            build_log = diagnostic
            assert "ssh-ng://" in build_log and "builder" in build_log, build_log

    with subtest("unsupported kvm builder is rejected without local fallback"):
        status, build_log = coordinator.execute("timeout 30 nix-build /etc/distributed-proof.nix --argstr mode kvm --no-out-link 2>&1")
        assert status != 0 and status != 124, (status, build_log)
        assert "kvm" in build_log, build_log
        output = coordinator.succeed("nix-instantiate --eval --strict /etc/distributed-proof.nix --argstr mode kvm -A outPath").strip().strip('"')
        for node in [coordinator, builder]:
            node.fail("nix-store --check-validity " + output)
  '';
}
