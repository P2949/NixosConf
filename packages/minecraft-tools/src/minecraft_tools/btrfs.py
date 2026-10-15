"""Filesystem identity checks and bounded Btrfs operations."""
import fcntl
import os
import re
import stat
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from .errors import BackupError
from .metadata import checked_uuid, checked_snapshot_path
DEFAULT_PREFLIGHT_TIMEOUT = 10.0
DEFAULT_SNAPSHOT_TIMEOUT = 60.0
SNAPSHOT_PREFIX = "survival-"


@dataclass(frozen=True)
class SnapshotPlan:
    source: Path
    destination: Path



def mounted_paths(mountinfo=Path("/proc/self/mountinfo")):
    paths = set()
    for line in mountinfo.read_text().splitlines():
        fields = line.split()
        if len(fields) < 6:
            raise BackupError("malformed mount table")
        mounted = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), fields[4])
        if not Path(mounted).is_absolute():
            raise BackupError("non-absolute mount path")
        paths.add(Path(mounted))
    return paths



def is_mountpoint(path, mountinfo=Path("/proc/self/mountinfo")):
    # ismount() also reports unmounted Btrfs subvolumes as mount points.
    return Path(os.path.abspath(path)) in mounted_paths(mountinfo)



def reject_nested_mounts(source):
    target = Path(os.path.abspath(source))
    if any(target in mounted.parents for mounted in mounted_paths()):
        raise BackupError("nested Minecraft mounts are not covered by snapshots", reason="nested-mount")



def snapshot_destination(
    snapshot_root: Path = None,
    now: datetime | None = None,
) -> Path:
    if snapshot_root is None:
        raise BackupError("explicit deployment policy values are required")
    if now is None:
        now = datetime.now(timezone.utc)

    if now.tzinfo is None:
        raise BackupError("snapshot timestamp must be timezone-aware")

    timestamp = now.astimezone(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    return snapshot_root / f"{SNAPSHOT_PREFIX}{timestamp}"



def run_btrfs_preflight(
    arguments,
    runner=subprocess.run,
    timeout: float = DEFAULT_PREFLIGHT_TIMEOUT,
):
    try:
        return runner(
            arguments,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise BackupError(
            "Btrfs preflight command timed out: "
            + " ".join(map(str, arguments))
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise BackupError(
            "Btrfs preflight command failed: "
            + " ".join(map(str, arguments))
        ) from exc



def verify_btrfs_subvolume(
    path: Path,
    runner=subprocess.run,
    timeout: float = DEFAULT_PREFLIGHT_TIMEOUT,
) -> None:
    run_btrfs_preflight(
        [
            "btrfs",
            "subvolume",
            "show",
            os.fspath(path),
        ],
        runner=runner,
        timeout=timeout,
    )



def btrfs_filesystem_uuid(
    path: Path,
    runner=subprocess.run,
    timeout: float = DEFAULT_PREFLIGHT_TIMEOUT,
) -> str:
    try:
        result = run_btrfs_preflight(
            ["btrfs", "filesystem", "show", "--raw", os.fspath(path)],
            runner=runner,
            timeout=timeout,
        )
    except BackupError as exc:
        if not isinstance(exc.__cause__, subprocess.CalledProcessError):
            raise
        # filesystem show requires a mountpoint and device access; retained
        # subvolumes and systemd's read-only namespace need a direct FS_INFO
        # query instead. Linux UAPI: _IOR(0x94, 31, 1024), fsid at bytes 16:32.
        # Opening read-only never weakens the service's filesystem sandbox.
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            info = bytearray(1024)
            fcntl.ioctl(descriptor, 0x8400941F, info, True)
            return checked_uuid(str(UUID(bytes=bytes(info[16:32]))))
        except OSError as ioctl_error:
            raise BackupError("cannot determine Btrfs filesystem identity") from ioctl_error
        finally:
            os.close(descriptor)

    if not isinstance(result.stdout, str):
        raise BackupError(
            f"Btrfs filesystem query returned non-text output for {path}"
        )

    filesystem_uuids = []

    for line in result.stdout.splitlines():
        match = re.search(
            r"\buuid:\s*(\S+)\s*$",
            line,
            flags=re.IGNORECASE,
        )

        if match is None:
            if line.lstrip().lower().startswith("label:"):
                raise BackupError("malformed Btrfs filesystem header")
            continue

        try:
            filesystem_uuids.append(
                checked_uuid(str(UUID(match.group(1))))
            )
        except ValueError as exc:
            raise BackupError("malformed Btrfs filesystem UUID") from exc

    if len(filesystem_uuids) != 1:
        raise BackupError(
            f"could not determine exactly one Btrfs filesystem UUID for {path}"
        )

    return filesystem_uuids[0]



def verify_source_completeness(source, runner=subprocess.run,
                               timeout=DEFAULT_PREFLIGHT_TIMEOUT):
    reject_nested_mounts(source)
    verify_btrfs_subvolume(source, runner=runner, timeout=timeout)
    descendants = run_btrfs_preflight(
        ["btrfs", "subvolume", "list", "-o", str(source)], runner=runner, timeout=timeout,
    )
    if descendants.stdout.strip():
        raise BackupError("nested Minecraft subvolumes are not covered by snapshots",
                          reason="nested-subvolume")



def prepare_snapshot(
    source: Path = None,
    snapshot_mount: Path = None,
    snapshot_root: Path = None,
    now: datetime | None = None,
    runner=subprocess.run,
    mount_checker=is_mountpoint,
    timeout: float = DEFAULT_PREFLIGHT_TIMEOUT,
) -> SnapshotPlan:
    if source is None or snapshot_mount is None or snapshot_root is None:
        raise BackupError("explicit deployment policy values are required")
    if source.is_symlink():
        raise BackupError(
            f"Minecraft source must not be a symbolic link: {source}", reason="mount-missing"
        )

    if not source.is_dir():
        raise BackupError(
            f"Minecraft source directory does not exist: {source}", reason="mount-missing"
        )

    if not mount_checker(source):
        raise BackupError(
            f"Minecraft source must be a mount point: {source}", reason="mount-missing"
        )

    if snapshot_mount.is_symlink():
        raise BackupError(
            f"snapshot mount must not be a symbolic link: {snapshot_mount}", reason="mount-missing"
        )

    if not snapshot_mount.is_dir():
        raise BackupError(
            f"snapshot mount does not exist: {snapshot_mount}", reason="mount-missing"
        )

    if not mount_checker(snapshot_mount):
        raise BackupError(
            f"snapshot path must be a mount point: {snapshot_mount}", reason="mount-missing"
        )

    if snapshot_root.parent != snapshot_mount:
        raise BackupError(
            "snapshot root must be a direct child of the snapshot mount"
        )

    verify_source_completeness(source, runner=runner, timeout=timeout)

    source_uuid = btrfs_filesystem_uuid(
        source,
        runner=runner,
        timeout=timeout,
    )
    snapshot_uuid = btrfs_filesystem_uuid(
        snapshot_mount,
        runner=runner,
        timeout=timeout,
    )

    if source_uuid != snapshot_uuid:
        raise BackupError(
            "Minecraft source and snapshot destination are on "
            "different Btrfs filesystems", reason="filesystem-mismatch"
        )

    if snapshot_root.is_symlink():
        raise BackupError(
            f"snapshot root must not be a symbolic link: {snapshot_root}"
        )

    try:
        snapshot_root.mkdir(
            mode=0o700,
            parents=False,
            exist_ok=True,
        )
    except OSError as exc:
        raise BackupError(
            f"cannot prepare snapshot root {snapshot_root}: {exc}"
        ) from exc

    if snapshot_root.is_symlink():
        raise BackupError(
            f"snapshot root must not be a symbolic link: {snapshot_root}"
        )

    if mount_checker(snapshot_root):
        raise BackupError(
            f"snapshot root must not be a mount point: {snapshot_root}"
        )

    if not snapshot_root.is_dir():
        raise BackupError(
            f"snapshot root is not a directory: {snapshot_root}"
        )

    if snapshot_root.lstat().st_uid != os.geteuid():
        raise BackupError("snapshot root must be owned by the backup user")

    try:
        snapshot_root.chmod(0o700)
    except OSError as exc:
        raise BackupError(
            f"cannot secure snapshot root {snapshot_root}: {exc}"
        ) from exc

    destination = snapshot_destination(
        snapshot_root=snapshot_root,
        now=now,
    )

    if os.path.lexists(destination):
        raise BackupError(
            f"snapshot destination already exists: {destination}"
        )

    return SnapshotPlan(
        source=source,
        destination=destination,
    )



def create_readonly_snapshot(
    plan: SnapshotPlan,
    runner=subprocess.run,
    timeout: float = DEFAULT_SNAPSHOT_TIMEOUT,
) -> Path:
    runner(
        [
            "btrfs",
            "subvolume",
            "snapshot",
            "-r",
            os.fspath(plan.source),
            os.fspath(plan.destination),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    return plan.destination



def verify_snapshot_root(snapshot_root, mount_checker):
    info = snapshot_root.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o700 or mount_checker(snapshot_root)):
        raise BackupError("snapshot root must be an owned unmounted mode 0700 directory")



def verify_snapshot_identity(path, filesystem_uuid, snapshot_root=None,
                             runner=subprocess.run, mount_checker=is_mountpoint):
    if snapshot_root is None:
        raise BackupError("explicit deployment policy values are required")
    checked_snapshot_path(str(path), snapshot_root)
    verify_snapshot_root(snapshot_root, mount_checker)
    if path.is_symlink() or not path.is_dir() or mount_checker(path):
        raise BackupError("snapshot must be an unmounted real subvolume")
    result = run_btrfs_preflight(["btrfs", "subvolume", "show", str(path)], runner=runner)
    matches = re.findall(r"^\s*UUID:\s*(\S+)\s*$", result.stdout, flags=re.MULTILINE)
    if len(matches) != 1:
        raise BackupError("could not determine exactly one snapshot UUID")
    identity = checked_uuid(matches[0])
    if btrfs_filesystem_uuid(path, runner=runner) != filesystem_uuid:
        raise BackupError("snapshot filesystem UUID mismatch", reason="filesystem-mismatch")
    result = run_btrfs_preflight(["btrfs", "property", "get", "-t", "s", str(path), "ro"], runner=runner)
    if result.stdout.strip() != "ro=true":
        raise BackupError("snapshot is not read-only", reason="snapshot-not-readonly")
    return identity



def sync_snapshot_filesystem(snapshot_mount, runner=subprocess.run):
    started = time.monotonic()
    runner(["btrfs", "filesystem", "sync", str(snapshot_mount)],
           check=True, capture_output=True, text=True,
           timeout=DEFAULT_SNAPSHOT_TIMEOUT)
    print(f"snapshot filesystem sync completed in {time.monotonic() - started:.3f} seconds", flush=True)

