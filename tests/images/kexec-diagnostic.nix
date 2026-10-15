{ inputs, pkgs }:
let
  diagnostic = inputs.self.nixosConfigurations.diagnostic.config;
in
pkgs.testers.runNixOSTest {
  name = "kexec-diagnostic";
  nodes.machine = {
    virtualisation = {
      memorySize = 4096;
      graphics = false;
      qemu.consoles = [ "ttyS0,115200n8" ];
      qemu.options = [ "-vga none" ];
    };
  };
  testScript = ''
    import re

    start_all()
    machine.wait_for_unit("multi-user.target")
    old_boot = machine.succeed("cat /proc/sys/kernel/random/boot_id").strip()
    machine.succeed("touch /run/before-kexec")
    machine.succeed("test $(hostname) = machine")
    machine.succeed("test -s ${diagnostic.system.build.kexecTree}/bzImage")
    machine.succeed("test -s ${diagnostic.system.build.kexecTree}/initrd.gz")
    # Only this disposable QEMU guest executes the native netboot entry script.
    # The diagnostic image carries no guest agent or injected test credential.
    machine.execute("${diagnostic.system.build.kexecTree}/kexec-boot", check_output=False)
    retry(lambda _: "DIAGNOSTIC_READY" in machine.get_console_log()
        or "Failed to start diagnostic-ready.service" in machine.get_console_log(), 180)
    evidence = machine.get_console_log()
    assert "DIAGNOSTIC_READY" in evidence, evidence[-6000:]
    boots = re.findall(r"DIAGNOSTIC_BOOT_ID=([0-9a-f-]{36})", evidence)
    assert len(boots) == 1, boots
    assert boots[0] != old_boot, (old_boot, boots)
    machine.crash()
  '';
}
