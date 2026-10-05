{ pkgs }:
pkgs.testers.runNixOSTest {
  name = "activation-safety-actions";
  nodes.machine = { lib, pkgs, ... }: {
    system.switch.enable = lib.mkForce true;
    system.preSwitchChecks.activation-fixture = ''
      printf '%s\n' "$2" > /run/pre-switch-action
      if test -e /run/refuse-activation; then
        echo "activation-fixture refused" >&2
        exit 1
      fi
    '';
    # Exercise native action dispatch without installing a real bootloader.
    # Actual disk reconstruction/UEFI acceptance is a separate required test.
    system.build.installBootLoader = lib.mkForce (
      pkgs.writeShellScript "fixture-bootloader" ''
        touch /run/fixture-bootloader-called
      ''
    );
    system.stateVersion = "26.05";
  };
  testScript = ''
    machine.start()
    machine.wait_for_unit("multi-user.target")
    current = machine.succeed("readlink -f /run/current-system").strip()
    for action in ["test", "boot", "switch", "dry-activate"]:
        machine.succeed("rm -f /run/fixture-bootloader-called")
        machine.succeed("touch /run/refuse-activation")
        status, output = machine.execute(f"{current}/bin/switch-to-configuration {action} 2>&1")
        assert status != 0 and "activation-fixture refused" in output, (action, status, output)
        machine.succeed("test ! -e /run/fixture-bootloader-called")
        machine.succeed("rm /run/refuse-activation")
        machine.succeed(f"{current}/bin/switch-to-configuration {action}")
        assert machine.succeed("cat /run/pre-switch-action").strip() == action
        if action in ["boot", "switch"]:
            machine.succeed("test -e /run/fixture-bootloader-called")
    machine.succeed("test -z \"$(systemctl --failed --no-legend --plain)\"")
  '';
}
