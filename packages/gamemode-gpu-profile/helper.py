"""GameMode owns Gaming only until the last client exits; preserve manual changes."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import socket
import stat
import sys
import tempfile


def api(command, args=None):
    request = {"command": command}
    if args is not None:
        request["args"] = args
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(5)
        connection.connect("/run/lactd.sock")
        connection.sendall((json.dumps(request) + "\n").encode())
        reply = json.loads(connection.makefile("r").readline(1024 * 1024))
    if reply["status"] != "ok":
        raise RuntimeError(f"LACT {command} failed: {reply}")
    return reply.get("data")


def identity():
    """A restarted GameMode daemon must not inherit another daemon's claim."""
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    owners = []
    for process in Path("/proc").iterdir():
        if not process.name.isdecimal():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            raw = (process / "stat").read_text()
            name, rest = raw[raw.index("(") + 1:].rsplit(")", 1)
            if name == "gamemoded" or name.startswith(".gamemoded"):
                owners.append([int(process.name), rest.split()[19]])
        except (OSError, ValueError, IndexError):
            continue
    return {"boot": boot, "daemons": sorted(owners)}


def select(profile):
    api("set_profile", {"name": profile, "auto_switch": False})
    assert api("list_profiles", {"include_state": True})["current_profile"] == profile, "LACT selection readback differs"


def transition(operation, directory, query=api, choose=select, owner=None):
    owner = identity() if owner is None else owner
    directory.mkdir(mode=0o700, exist_ok=True)
    info = directory.lstat()
    assert stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700, "Unsafe runtime state directory"
    lock_fd = os.open(directory / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = directory / "state.json"
        assert not path.is_symlink(), "Unsafe runtime state symlink"
        state = json.loads(path.read_text()) if path.exists() else None
        if state and state["owner"] != owner:
            print("gamemode-gpu-profile: discarding stale owner state", file=sys.stderr)
            path.unlink()
            state = None
        if operation == "end" and state is None:
            return
        current = query("list_profiles", {"include_state": True})
        assert not current["auto_switch"], "LACT auto-switch must remain disabled"
        profile = current["current_profile"]
        if operation == "start":
            if state is not None:
                return  # Duplicate callback must not replace the saved profile.
            assert "Gaming" in current["profiles"], "Gaming profile is missing"
            state = {"version": 1, "owner": owner, "previous": profile}
            descriptor, temporary_name = tempfile.mkstemp(prefix="state-", dir=directory)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "w") as stream:
                    json.dump(state, stream)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
            if profile != "Gaming":
                choose("Gaming")  # State retained if selection fails ambiguously.
        else:
            if profile == "Gaming" and state["previous"] != "Gaming":
                choose(state["previous"])
            elif profile != "Gaming":
                print("gamemode-gpu-profile: preserving externally selected profile", file=sys.stderr)
            path.unlink()  # Keep the receipt on query/selection failure for diagnosis.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["start", "end"])
    args = parser.parse_args()
    try:
        runtime = Path(os.environ["XDG_RUNTIME_DIR"])
        assert runtime.is_absolute() and runtime.stat().st_uid == os.getuid(), "Invalid user runtime directory"
        transition(args.operation, runtime / "gamemode-gpu-profile")
    except Exception as error:
        print(f"gamemode-gpu-profile: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
