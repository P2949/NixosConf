"""Explicit physical boot receipts; never changes boot selection or reboots."""
import datetime
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import uuid


def fail(message):
    raise SystemExit(message)


def fsroot(path):
    return subprocess.check_output(
        ["findmnt", "-rn", "-o", "FSROOT", "-T", str(path)], text=True
    ).strip()


def write_user_file(path, token, username):
    subprocess.run(
        ["runuser", "-u", username, "--", sys.executable, "-c",
         "import pathlib,sys; p=pathlib.Path(sys.argv[1]); "
         "p.parent.mkdir(parents=True,exist_ok=True); p.write_text(sys.argv[2])",
         str(path), token], check=True
    )


def proof_target(directory, leaf):
    target = Path(directory) / leaf
    # Codex snapshot and Firefox telemetry cleanup skip directories, but delete
    # unknown regular files. Keep proofs inside those same reset-backed mounts.
    parts = Path(directory).parts
    if (
        parts[-2:] == (".codex", "shell_snapshots")
        or parts[-4:] == (".config", "mozilla", "firefox", "Pending Pings")
        or (parts[-5:-2] == (".config", "mozilla", "firefox")
            and parts[-1] == "saved-telemetry-pings")
    ):
        return target / "token", target
    return target, None


def sentinel_errors(items, token):
    errors = []
    for item in items:
        target = Path(item["path"])
        container = Path(item["container"]) if item.get("container") else None
        if container and (target.parent != container or
                          container.name != "granular-impermanence-proof-" + token):
            errors.append(f"Invalid generated sentinel container: {container}")
            continue
        if item["retained"]:
            if not target.is_file() or target.read_text() != token:
                errors.append(f"Declared/recovery sentinel lost: {target}")
        elif target.exists() or (container and container.exists()):
            errors.append(f"Ephemeral sentinel survived: {target}")
    return errors


def remove_retained_sentinels(items):
    for item in items:
        if item["retained"]:
            Path(item["path"]).unlink()
            if item.get("container"):
                # Only remove this generated directory if empty; never recurse.
                Path(item["container"]).rmdir()


def main():
    if os.geteuid() != 0:
        fail("Run as root to check system sentinels and private migration receipts.")
    settings = json.loads(Path(sys.argv[1]).read_text())
    args = sys.argv[2:]
    if not args or args[0] not in ("seed", "verify"):
        fail("Usage: granular-physical-check seed home|home-recovery|normal|recovery SYSTEM | verify")

    evidence = Path("/persist/granular-migration")
    evidence.mkdir(mode=0o700, exist_ok=True)
    os.umask(0o077)
    ticket = evidence / "physical-boot-pending.json"
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    home = Path(settings["home"])

    if args[0] == "seed":
        if len(args) != 3 or args[1] not in ("home", "home-recovery", "normal", "recovery"):
            fail("seed requires a migration mode and the exact next system closure.")
        if ticket.exists():
            fail("A physical boot check is already pending; verify it before seeding another.")
        mode = args[1]
        recovery = mode in ("recovery", "home-recovery")
        system = str(Path(args[2]).resolve())
        if not system.startswith("/nix/store/") or not Path(system, "bin/switch-to-configuration").is_file():
            fail("The next system must be an already built NixOS store closure.")
        token = str(uuid.uuid4())
        leaf = "granular-impermanence-proof-" + token
        paths = []
        root_dirs = ["/etc", "/root", "/tmp", "/srv", "/usr/local"]
        var_dirs = ["/var/cache", "/var/tmp", "/var/lib/granular-undeclared"]
        home_dirs = [home / ".cache", home / "granular-undeclared"]
        home_dirs += [home / relative for relative in settings["caches"]]
        for directories, retained, user_owned in [
            (root_dirs, recovery, False),
            (var_dirs, mode != "normal", False),
            (home_dirs, recovery, True),
            ([home / "Documents", home / ".config/Code"], True, True),
            (["/persist", "/nix", "/.snapshots", "/boot",
              "/var/lib/nixos", "/var/lib/nixos-optimization"], True, False),
        ]:
            for directory in directories:
                target, container = proof_target(directory, leaf)
                if user_owned:
                    write_user_file(target, token, settings["username"])
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(token)
                item = {"path": str(target), "retained": retained}
                if container:
                    item["container"] = str(container)
                paths.append(item)
        data = {"boot_id": boot_id, "mode": mode, "system": system,
                "seeded_home_fsroot": fsroot(home),
                "token": token, "paths": paths,
                "machine_id": Path("/etc/machine-id").read_text().strip()}
        ticket.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Seeded {len(paths)} sentinels for {mode}; pending receipt: {ticket}")
    else:
        if len(args) != 1 or not ticket.exists():
            fail("verify requires an existing pending physical boot receipt.")
        data = json.loads(ticket.read_text())
        if data["boot_id"] == boot_id:
            fail("The workstation has not rebooted since these sentinels were seeded.")
        errors = []
        if str(Path("/run/current-system").resolve()) != data["system"]:
            errors.append("The booted system differs from the exact expected closure.")
        if fsroot(home) != "/@root":
            errors.append("Home is not root-local.")
        expected_var = "/@var" if data["mode"] in ("home", "home-recovery") else "/@root"
        if fsroot("/var") != expected_var:
            errors.append("Var topology differs from the expected migration phase.")
        for mount, expected in [("/", "/@root"), ("/persist", "/@persist"),
                                ("/nix", "/@nix"), ("/.snapshots", "/@snapshots"),
                                ("/var/lib/nixos-optimization", "/@optimization")]:
            if fsroot(mount) != expected:
                errors.append(f"Incorrect persistent/root island: {mount}")
        if Path("/etc/machine-id").read_text().strip() != data["machine_id"]:
            errors.append("Machine identity changed.")
        owner = pwd.getpwnam(settings["username"]).pw_uid
        if (home / ".cache").stat().st_uid != owner:
            errors.append("The home cache root is not owned by the user.")
        errors.extend(sentinel_errors(data["paths"], data["token"]))
        if errors:
            fail("Physical check failed; pending receipt retained:\n" + "\n".join(errors))
        data["verified_boot_id"] = boot_id
        data["verified_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt = evidence / ("physical-boot-passed-" + data["token"] + ".json")
        receipt.write_text(json.dumps(data, indent=2) + "\n")
        remove_retained_sentinels(data["paths"])
        ticket.unlink()
        print(f"Physical {data['mode']} boot check passed; receipt: {receipt}")


if __name__ == "__main__":
    main()
