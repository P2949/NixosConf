{ inputs, pkgs }:
let
  appliance = inputs.self.nixosConfigurations.benchmark-appliance.config;
in
pkgs.testers.runNixOSTest {
  name = "benchmark-appliance-integrity";
  nodes.machine = {
    virtualisation = {
      directBoot.enable = false;
      useEFIBoot = true;
      mountHostNixStore = false;
      graphics = false;
      memorySize = 2048;
      cores = 2;
      qemu.consoles = [ "ttyS0,115200n8" ];
      qemu.options = [ "-vga none" ];
    };
  };
  testScript = { nodes, ... }: ''
    import hashlib
    import json
    import os
    from pathlib import Path
    import re
    import shutil
    import subprocess
    import tempfile

    # Boot the exact standalone image; no guest agent or test credentials are
    # injected into it. Readiness and corruption are observed on its console.
    original = Path("${appliance.system.build.image}/${appliance.image.filePath}")
    partitions = json.loads(Path("${appliance.system.build.image}/repart-output.json").read_text())
    data = next(part for part in partitions if part.get("label") == "store")
    assert data["type"] == "usr-x86-64", data
    offset = int(data["offset"]) + 1024
    assert int(data["offset"]) <= offset < int(data["offset"]) + int(data["raw_size"])

    def digest(path):
        value = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(block)
        return value.hexdigest()

    def overlay(destination, backing):
        subprocess.run(["${nodes.machine.virtualisation.qemu.package}/bin/qemu-img", "create", "-f", "qcow2", "-F", "raw", "-b", str(backing), str(destination)], check=True)

    def wait_console(pattern, timeout=180):
        # The driver's queue-based helper consumes only one line per second.
        # Match the complete current boot log so verbose boots cannot exhaust
        # the deadline while the required evidence is already available.
        retry(lambda _: re.search(pattern, machine.get_console_log()) is not None, timeout)

    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        pristine = digest(original)
        overlay(work / "healthy.qcow2", original)
        os.environ["NIX_DISK_IMAGE"] = str(work / "healthy.qcow2")
        machine.start()
        wait_console("BENCHMARK_APPLIANCE_READY")
        wait_console("Reached target.*Multi-User System", timeout=60)
        machine.crash()

        damaged = work / "damaged.raw"
        shutil.copyfile(original, damaged)
        assert not str(damaged.resolve()).startswith("/nix/store/")
        with damaged.open("r+b") as stream:
            stream.seek(offset)
            byte = stream.read(1)
            assert len(byte) == 1
            stream.seek(offset)
            stream.write(bytes([byte[0] ^ 1]))
        assert digest(original) == pristine
        assert digest(damaged) != pristine
        overlay(work / "damaged.qcow2", damaged)
        os.environ["NIX_DISK_IMAGE"] = str(work / "damaged.qcow2")
        machine.start()
        wait_console("device-mapper: verity:.*data block.*corrupt")
        wait_console("Kernel panic.*dm-verity device corrupted", timeout=60)
        machine.crash()
        assert digest(original) == pristine
        print("CORRUPTION_DETECTED: protected data byte changed; original store image unchanged")
  '';
}
