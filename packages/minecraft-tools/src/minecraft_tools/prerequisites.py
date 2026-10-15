"""Read-only physical activation prerequisites; never emit credential contents."""

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

from minecraft_tools.config import load_config


class PrerequisiteError(RuntimeError):
    pass


def mount_record(path, runner=subprocess.run):
    if Path(path).is_symlink() or not Path(path).is_dir():
        raise PrerequisiteError("required mount directory is invalid")
    result = runner(
        [
            "findmnt",
            "--json",
            "--mountpoint",
            path,
            "--output",
            "TARGET,FSTYPE,FSROOT,UUID,OPTIONS",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    records = json.loads(result.stdout).get("filesystems", [])
    if len(records) != 1 or records[0].get("target") != path:
        raise PrerequisiteError("required physical mount is absent")
    return records[0]


def validate_mounts(root, minecraft, snapshots, source_fs_root, snapshot_fs_root):
    identities = []
    for record, fsroot in (
        (root, None),
        (minecraft, source_fs_root),
        (snapshots, snapshot_fs_root),
    ):
        if record.get("fstype") != "btrfs":
            raise PrerequisiteError("required filesystem is not Btrfs")
        if fsroot is not None and record.get("fsroot") != fsroot:
            raise PrerequisiteError(
                "physical subvolume does not match desired topology"
            )
        options = record.get("options", "").split(",")
        if "rw" not in options or "ro" in options:
            raise PrerequisiteError("required filesystem is not writable")
        identity = record.get("uuid")
        if (
            not isinstance(identity, str)
            or not re.fullmatch(
                r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", identity
            )
            or not int(identity.replace("-", ""), 16)
        ):
            raise PrerequisiteError("filesystem identity is unavailable")
        identities.append(identity.lower())
    if len(set(identities)) != 1:
        raise PrerequisiteError(
            "Minecraft, root and snapshots must share the Btrfs filesystem"
        )


def validate_secret(path, owner=0, group=0):
    directory = path.parent
    info = directory.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != owner
        or info.st_gid != group
        or stat.S_IMODE(info.st_mode) != 0o700
    ):
        raise PrerequisiteError("secret directory must be root-owned mode 0700")
    parent = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        descriptor = os.open(
            path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
        )
        try:
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != owner
                or info.st_gid != group
                or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != 0o600
            ):
                raise PrerequisiteError(
                    "secret file must be root-owned regular mode 0600 with one link"
                )
            value = os.read(descriptor, 4097)
            if (
                re.fullmatch(rb"MINECRAFT_MANAGEMENT_SECRET=[A-Za-z0-9]{40}\n?", value)
                is None
            ):
                raise PrerequisiteError("secret assignment format is invalid")
        finally:
            os.close(descriptor)
    finally:
        os.close(parent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        validate_mounts(
            mount_record("/"),
            mount_record(str(config.source)),
            mount_record(str(config.snapshot_mount)),
            config.source_fs_root,
            config.snapshot_fs_root,
        )
        validate_secret(config.environment_file)
    except Exception:
        print(
            "Minecraft activation refused: prepare physical Btrfs mounts and root-only management secret; see docs/minecraft-server.md",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
