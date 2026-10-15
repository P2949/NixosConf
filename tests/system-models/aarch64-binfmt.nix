{ pkgs }:
let
  native = pkgs.hello;
  aarch64 = pkgs.pkgsCross.aarch64-multiplatform.hello;
in
pkgs.testers.runNixOSTest {
  name = "aarch64-binfmt-packaging";
  nodes.machine = {
    boot.binfmt.emulatedSystems = [ "aarch64-linux" ];
    virtualisation = {
      graphics = false;
      qemu.options = [ "-vga none" ];
    };
  };
  testScript = ''
    start_all()
    machine.wait_for_unit("systemd-binfmt.service")
    assert machine.succeed("uname -m").strip() == "x86_64"
    machine.succeed("${pkgs.binutils}/bin/readelf -h ${native}/bin/hello | grep -q 'Machine:.*X86-64'")
    machine.succeed("${pkgs.binutils}/bin/readelf -h ${aarch64}/bin/hello | grep -q 'Machine:.*AArch64'")
    registration = "/proc/sys/fs/binfmt_misc/aarch64-linux"
    assert machine.succeed(f"head -n 1 {registration}").strip() == "enabled"
    assert "interpreter /run/binfmt/aarch64-linux" in machine.succeed(f"cat {registration}")

    with subtest("native and cross-built package execute directly"):
        expected = machine.succeed("LC_ALL=C ${native}/bin/hello")
        assert expected.strip() == "Hello, world!"
        assert machine.succeed("LC_ALL=C ${aarch64}/bin/hello") == expected

    with subtest("foreign execution requires its kernel registration"):
        machine.succeed(f"echo -1 > {registration}")
        status, output = machine.execute("LC_ALL=C ${aarch64}/bin/hello 2>&1")
        assert status != 0, output
        assert "Exec format error" in output, output
        # The native package continues to execute while the foreign rule is absent.
        assert machine.succeed("LC_ALL=C ${native}/bin/hello") == expected
        machine.succeed("systemctl restart systemd-binfmt.service")
        assert machine.succeed(f"head -n 1 {registration}").strip() == "enabled"
        assert machine.succeed("LC_ALL=C ${aarch64}/bin/hello") == expected
  '';
}
