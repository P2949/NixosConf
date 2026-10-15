{ pkgs }:
pkgs.testers.runNixOSTest {
  name = "immutable-etc-userborn-perlless";
  nodes.machine =
    {
      config,
      lib,
      modulesPath,
      ...
    }:
    {
      imports = [ "${modulesPath}/profiles/perlless.nix" ];
      system.etc.overlay.mutable = false;
      networking.useNetworkd = true;
      services.resolved.enable = true;
      # Synthetic guest identity: immutable /etc must already contain this file
      # before PID 1 and D-Bus start. Never copy the workstation's identity.
      environment.etc."machine-id" = {
        text = "c18dbaea46f44781b55a1ae69a330001\n";
        mode = "0444";
      };
      users.mutableUsers = false;
      users.groups.model-service.gid = 2400;
      users.users.model-service = {
        isSystemUser = true;
        uid = 2400;
        group = "model-service";
      };
      environment.etc."model-version".text = "one\n";
      systemd.services.model-proof = {
        wantedBy = [ "multi-user.target" ];
        after = [ "userborn.service" ];
        requires = [ "userborn.service" ];
        restartTriggers = [ config.environment.etc."model-version".text ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
          User = "model-service";
          Group = "model-service";
          StateDirectory = "model-proof";
        };
        script = ''
          cat /etc/model-version > /var/lib/model-proof/result
          id -u > /var/lib/model-proof/uid
        '';
      };
      specialisation.updated.configuration = {
        environment.etc."model-version".text = lib.mkForce "two\n";
        users.users.model-service.description = lib.mkForce "Updated declarative service user";
        users.users.model-added = {
          isSystemUser = true;
          uid = 2401;
          group = "model-service";
        };
      };
      virtualisation = {
        mountHostNixStore = false;
        useNixStoreImage = true;
        graphics = false;
        qemu.options = [ "-vga none" ];
      };
    };
  testScript = ''
    start_all()
    machine.wait_for_unit("model-proof.service")
    original = machine.succeed("readlink -f /run/current-system").strip()

    def check(version):
        machine.wait_for_unit("userborn.service")
        machine.wait_for_unit("dbus.service")
        machine.wait_for_unit("systemd-networkd.service")
        machine.wait_for_unit("systemd-resolved.service")
        machine.wait_for_unit("model-proof.service")
        machine.succeed(f"test $(cat /etc/model-version) = {version}")
        machine.succeed(f"test $(cat /var/lib/model-proof/result) = {version}")
        machine.succeed("test $(cat /var/lib/model-proof/uid) = 2400")
        machine.succeed("test $(id -u model-service) = 2400")
        machine.succeed("test $(stat -c %u /var/lib/model-proof/result) = 2400")
        machine.succeed("test $(readlink -f /etc/passwd) = /var/lib/nixos/passwd")
        machine.succeed("test $(cat /etc/machine-id) = c18dbaea46f44781b55a1ae69a330001")
        machine.succeed("findmnt --first-only --target /etc -n -o OPTIONS | grep -Eq '(^|,)ro(,|$)'")
        machine.fail("touch /etc/forbidden-write")
        machine.fail("sh -c 'echo changed >> /etc/model-version'")
        machine.succeed("test -z \"$(find /nix/store -maxdepth 1 -iname '*perl*' -print -quit)\"")
        machine.fail("command -v perl")

    with subtest("immutable boot and Userborn service account"):
        check("one")
        machine.fail("getent passwd model-added")

    with subtest("declarative switch replaces immutable etc and updates accounts"):
        machine.succeed(f"{original}/specialisation/updated/bin/switch-to-configuration switch")
        check("two")
        machine.succeed("test $(id -u model-added) = 2401")
        assert "Updated declarative service user" in machine.succeed("getent passwd model-service")

    with subtest("switch back restores configuration and service operation"):
        machine.succeed(f"{original}/bin/switch-to-configuration switch")
        check("one")
  '';
}
