#!/usr/bin/env python3

import fcntl
import importlib.util
import json
import stat
import tempfile
import time
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from websockets.exceptions import ConnectionClosed


SOURCE_SUBVOLUME = Path("/srv/minecraft")
SNAPSHOT_MOUNT = Path("/.snapshots")
SNAPSHOT_ROOT = SNAPSHOT_MOUNT / "minecraft"
SNAPSHOT_PREFIX = "survival-"
RECOVERY_DIRECTORY = Path("/run/minecraft-backup")
LOCK_FILE = RECOVERY_DIRECTORY / "backup.lock"
AUTOSAVE_RECOVERY_MARKER = (
    RECOVERY_DIRECTORY / "autosave-needs-restore"
)
STATE_DIRECTORY = Path("/persist/minecraft-backup")
KEEP_SNAPSHOTS = 14
MAX_RETENTION_DELETIONS_PER_RUN = 4
HEALTH_FAILURE_MESSAGE = "backup failed; inspect stage and service journal"
HEALTH_FAILURE_STAGES = {
    "environment-preflight", "reconciliation", "preflight", "readiness", "pending-state", "consistency-transaction", "durability-sync", "registration", "retention",
}
DEFAULT_PREFLIGHT_TIMEOUT = 10.0
DEFAULT_SNAPSHOT_TIMEOUT = 60.0


@dataclass(frozen=True)
class SnapshotPlan:
    source: Path
    destination: Path


DIAGNOSTIC_REASONS = frozenset({
    "operation-failed", "unexpected-error", "mount-missing", "filesystem-mismatch",
    "nested-mount", "nested-subvolume", "management-unavailable", "management-incompatible",
    "snapshot-command-failed", "snapshot-timeout", "sync-command-failed", "sync-timeout",
    "btrfs-command-failed", "btrfs-timeout", "snapshot-identity-mismatch",
    "snapshot-not-readonly", "retention-integrity-failure", "metadata-invalid",
    "autosave-recovery-failed",
})


class BackupError(RuntimeError):
    def __init__(self, message, *, reason="operation-failed", stage=None):
        super().__init__(message)
        self.reason = reason if reason in DIAGNOSTIC_REASONS else "unexpected-error"
        self.stage = stage if stage in HEALTH_FAILURE_STAGES else None


def diagnostic_reason(error, stage=None):
    # Only trusted types/codes are inspected; never serialize exception text.
    if isinstance(error, BackupError) and error.reason != "operation-failed":
        return error.reason
    if isinstance(error, (subprocess.TimeoutExpired, subprocess.CalledProcessError)):
        prefix = {"durability-sync": "sync", "consistency-transaction": "snapshot"}.get(stage, "btrfs")
        suffix = "timeout" if isinstance(error, subprocess.TimeoutExpired) else "command-failed"
        return prefix + "-" + suffix
    if isinstance(error, (msmp.ProtocolError, msmp.RpcError, msmp.ConfigurationError)):
        return "management-incompatible"
    if isinstance(error, (TimeoutError, ConnectionClosed, ConnectionError)):
        return "management-unavailable"
    if error.__cause__ is not None:
        return diagnostic_reason(error.__cause__, stage)
    if stage == "retention":
        return "retention-integrity-failure"
    if isinstance(error, BackupError):
        return "operation-failed"
    return "unexpected-error"


class BackupRecoveryError(BackupError):
    def __init__(self, transaction_error, recovery_error):
        self.transaction_error = transaction_error
        self.recovery_error = recovery_error

        super().__init__(
            f"{transaction_error}; fresh-connection autosave recovery "
            f"also failed: {recovery_error}", reason="autosave-recovery-failed"
        )


def load_msmp():
    source_value = os.environ.get("MINECRAFT_MSMP_SOURCE")

    if source_value is None:
        raise BackupError("MINECRAFT_MSMP_SOURCE is not set")

    source = Path(source_value)

    spec = importlib.util.spec_from_file_location(
        "minecraft_msmp",
        source,
    )

    if spec is None or spec.loader is None:
        raise BackupError(
            f"cannot load Minecraft management client from {source}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


msmp = load_msmp()

DEFAULT_RPC_TIMEOUT = msmp.DEFAULT_RPC_TIMEOUT
DEFAULT_SAVE_TIMEOUT = msmp.DEFAULT_SAVE_TIMEOUT


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


@contextmanager
def exclusive_backup_lock(
    path: Path = LOCK_FILE,
):
    if path == LOCK_FILE:
        prepare_recovery_directory()
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC

    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        descriptor = os.open(
            path,
            flags,
            0o600,
        )
    except OSError as exc:
        raise BackupError(
            f"cannot open backup lock {path}: {exc}"
        ) from exc

    locked = False

    try:
        os.fchmod(descriptor, 0o600)

        try:
            fcntl.flock(
                descriptor,
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except BlockingIOError as exc:
            raise BackupError(
                "another Minecraft backup is already running"
            ) from exc

        locked = True
        yield

    finally:
        if locked:
            fcntl.flock(
                descriptor,
                fcntl.LOCK_UN,
            )

        os.close(descriptor)


def prepare_recovery_directory(
    directory: Path = RECOVERY_DIRECTORY,
) -> None:
    directory.mkdir(
        mode=0o700,
        parents=True,
        exist_ok=True,
    )

    if directory.is_symlink():
        raise BackupError(
            f"recovery directory must not be a symbolic link: {directory}"
        )

    directory.chmod(0o700)


def create_autosave_recovery_marker(
    marker: Path = AUTOSAVE_RECOVERY_MARKER,
) -> None:
    prepare_recovery_directory(
        directory=marker.parent,
    )

    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_CLOEXEC
    )

    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        descriptor = os.open(
            marker,
            flags,
            0o600,
        )
    except FileExistsError as exc:
        raise BackupError(
            f"autosave recovery marker already exists: {marker}"
        ) from exc
    except OSError as exc:
        raise BackupError(
            f"cannot create autosave recovery marker {marker}: {exc}"
        ) from exc

    try:
        os.fchmod(
            descriptor,
            0o600,
        )
        os.write(
            descriptor,
            b"autosave-needs-restore\n",
        )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def autosave_recovery_needed(
    marker: Path = AUTOSAVE_RECOVERY_MARKER,
) -> bool:
    try:
        status = marker.lstat()
    except FileNotFoundError:
        return False

    if marker.is_symlink():
        raise BackupError(
            f"autosave recovery marker must not be a symbolic link: {marker}"
        )

    if not marker.is_file():
        raise BackupError(
            f"autosave recovery marker is not a regular file: {marker}"
        )

    del status
    return True


def clear_autosave_recovery_marker(
    marker: Path = AUTOSAVE_RECOVERY_MARKER,
) -> None:
    try:
        marker.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise BackupError(
            f"cannot remove autosave recovery marker {marker}: {exc}"
        ) from exc


def snapshot_destination(
    snapshot_root: Path = SNAPSHOT_ROOT,
    now: datetime | None = None,
) -> Path:
    if now is None:
        now = datetime.now(timezone.utc)

    if now.tzinfo is None:
        raise BackupError("snapshot timestamp must be timezone-aware")

    timestamp = now.astimezone(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
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
    source: Path = SOURCE_SUBVOLUME,
    snapshot_mount: Path = SNAPSHOT_MOUNT,
    snapshot_root: Path = SNAPSHOT_ROOT,
    now: datetime | None = None,
    runner=subprocess.run,
    mount_checker=is_mountpoint,
    timeout: float = DEFAULT_PREFLIGHT_TIMEOUT,
) -> SnapshotPlan:
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


def restore_autosave_with_fresh_connection(
    connection_factory=msmp.open_connection,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
) -> None:
    with connection_factory() as websocket:
        recovery_session = msmp.MsmpSession(websocket)
        recovery_session.set_autosave(
            True,
            timeout=rpc_timeout,
        )


def recover_abandoned_autosave(
    marker: Path = AUTOSAVE_RECOVERY_MARKER,
    connection_factory=msmp.open_connection,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
) -> bool:
    if not autosave_recovery_needed(marker):
        return False

    restore_autosave_with_fresh_connection(
        connection_factory=connection_factory,
        rpc_timeout=rpc_timeout,
    )

    clear_autosave_recovery_marker(
        marker=marker,
    )

    return True


def perform_backup(
    action=create_readonly_snapshot,
    connection_factory=msmp.open_connection,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
    save_timeout: float = DEFAULT_SAVE_TIMEOUT,
    recovery_marker: Path = AUTOSAVE_RECOVERY_MARKER,
):
    recover_abandoned_autosave(
        marker=recovery_marker,
        connection_factory=connection_factory,
        rpc_timeout=rpc_timeout,
    )

    try:
        with connection_factory() as websocket:
            session = msmp.MsmpSession(websocket)

            return msmp.run_backup_transaction(
                session,
                action,
                rpc_timeout=rpc_timeout,
                save_timeout=save_timeout,
                before_autosave_disable=lambda: (
                    create_autosave_recovery_marker(
                        marker=recovery_marker,
                    )
                ),
                after_autosave_restore=lambda: (
                    clear_autosave_recovery_marker(
                        marker=recovery_marker,
                    )
                ),
            )

    except msmp.BackupTransactionError as transaction_error:
        try:
            restore_autosave_with_fresh_connection(
                connection_factory=connection_factory,
                rpc_timeout=rpc_timeout,
            )
            clear_autosave_recovery_marker(
                marker=recovery_marker,
            )
        except Exception as recovery_error:
            raise BackupRecoveryError(
                transaction_error,
                recovery_error,
            ) from recovery_error

        if transaction_error.primary_error is not None:
            primary_error = transaction_error.primary_error
            raise primary_error.with_traceback(
                primary_error.__traceback__
            )

        raise BackupError(
            "backup snapshot completed, but normal autosave restoration "
            "failed; autosave was recovered using a fresh connection"
        )


def perform_snapshot_backup(
    source: Path = SOURCE_SUBVOLUME,
    snapshot_mount: Path = SNAPSHOT_MOUNT,
    snapshot_root: Path = SNAPSHOT_ROOT,
    now: datetime | None = None,
    mount_checker=is_mountpoint,
    preflight_runner=subprocess.run,
    snapshot_runner=subprocess.run,
    preflight_timeout: float = DEFAULT_PREFLIGHT_TIMEOUT,
    snapshot_timeout: float = DEFAULT_SNAPSHOT_TIMEOUT,
    connection_factory=msmp.open_connection,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
    save_timeout: float = DEFAULT_SAVE_TIMEOUT,
    recovery_marker: Path = AUTOSAVE_RECOVERY_MARKER,
):
    recover_abandoned_autosave(
        marker=recovery_marker,
        connection_factory=connection_factory,
        rpc_timeout=rpc_timeout,
    )

    plan = prepare_snapshot(
        source=source,
        snapshot_mount=snapshot_mount,
        snapshot_root=snapshot_root,
        now=now,
        runner=preflight_runner,
        mount_checker=mount_checker,
        timeout=preflight_timeout,
    )

    return perform_backup(
        action=lambda: create_readonly_snapshot(
            plan,
            runner=snapshot_runner,
            timeout=snapshot_timeout,
        ),
        connection_factory=connection_factory,
        rpc_timeout=rpc_timeout,
        save_timeout=save_timeout,
        recovery_marker=recovery_marker,
    )


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def checked_object(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise BackupError("invalid persistent metadata fields", reason="metadata-invalid")


def checked_uuid(value):
    if not isinstance(value, str):
        raise BackupError("invalid persistent UUID", reason="metadata-invalid")
    try:
        if str(UUID(value)) != value or UUID(value).int == 0:
            raise ValueError()
    except ValueError as exc:
        raise BackupError("invalid persistent UUID", reason="metadata-invalid") from exc
    return value


def checked_time(value):
    if not isinstance(value, str):
        raise BackupError("invalid persistent UTC timestamp", reason="metadata-invalid")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
            raise ValueError()
    except ValueError as exc:
        raise BackupError("invalid persistent UTC timestamp", reason="metadata-invalid") from exc
    return value


def checked_snapshot_path(value, snapshot_root):
    if not isinstance(value, str):
        raise BackupError("invalid snapshot path", reason="metadata-invalid")
    path = Path(value)
    if (not path.is_absolute() or str(path) != value
            or path.parent != snapshot_root
            or re.fullmatch(r"survival-[0-9]{8}T[0-9]{6}Z", path.name) is None):
        raise BackupError("snapshot must be a named direct child of snapshot root", reason="metadata-invalid")
    try:
        datetime.strptime(path.name, "survival-%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise BackupError("invalid snapshot name timestamp", reason="metadata-invalid") from exc
    return path


def validate_record(record, snapshot_root):
    checked_object(record, ("name", "path", "created_at", "filesystem_uuid", "subvolume_uuid"))
    path = checked_snapshot_path(record["path"], snapshot_root)
    if record["name"] != path.name:
        raise BackupError("snapshot name does not match path", reason="metadata-invalid")
    checked_time(record["created_at"])
    checked_uuid(record["filesystem_uuid"])
    checked_uuid(record["subvolume_uuid"])


def validate_metadata(state, manifest, snapshot_root):
    checked_object(state, ("schema_version", "pending_snapshot", "pending_deletion", "last_attempt", "last_success", "last_retention"))
    checked_object(manifest, ("schema_version", "snapshots"))
    for value in (state, manifest):
        if type(value["schema_version"]) is not int or value["schema_version"] != 2:
            raise BackupError("unsupported persistent metadata schema", reason="metadata-invalid")
    if not isinstance(manifest["snapshots"], list):
        raise BackupError("managed snapshots must be a list", reason="metadata-invalid")
    paths, identities = set(), set()
    for record in manifest["snapshots"]:
        validate_record(record, snapshot_root)
        if record["path"] in paths or record["subvolume_uuid"] in identities:
            raise BackupError("duplicate managed snapshot identity", reason="metadata-invalid")
        paths.add(record["path"])
        identities.add(record["subvolume_uuid"])
    deletion = state["pending_deletion"]
    if deletion is not None:
        validate_record(deletion, snapshot_root)
        existing = next((r for r in manifest["snapshots"] if r["path"] == deletion["path"]), None)
        if existing is not None and existing != deletion:
            raise BackupError("deletion intent disagrees with manifest", reason="metadata-invalid")
        if state["last_success"] is not None and state["last_success"]["snapshot_path"] == deletion["path"]:
            raise BackupError("deletion intent targets last successful snapshot", reason="metadata-invalid")
        if state["pending_snapshot"] is not None and state["pending_snapshot"]["path"] == deletion["path"]:
            raise BackupError("deletion intent targets pending snapshot", reason="metadata-invalid")
    pending = state["pending_snapshot"]
    if pending is not None:
        checked_object(pending, ("path", "planned_at", "source_filesystem_uuid"))
        checked_snapshot_path(pending["path"], snapshot_root)
        checked_time(pending["planned_at"])
        checked_uuid(pending["source_filesystem_uuid"])
    success = state["last_success"]
    if success is not None:
        checked_object(success, ("created_at", "snapshot_path", "snapshot_uuid", "filesystem_uuid"))
        checked_time(success["created_at"])
        checked_snapshot_path(success["snapshot_path"], snapshot_root)
        checked_uuid(success["snapshot_uuid"])
        checked_uuid(success["filesystem_uuid"])
    attempt = state["last_attempt"]
    if attempt is not None:
        if not isinstance(attempt, dict) or attempt.get("result") not in ("success", "failed", "recovered", "aborted"):
            raise BackupError("invalid last attempt", reason="metadata-invalid")
        fields = ("started_at", "finished_at", "result")
        if attempt["result"] == "failed":
            fields += ("stage", "error_type", "message")
        checked_object(attempt, fields)
        checked_time(attempt["started_at"])
        checked_time(attempt["finished_at"])
        for field in fields:
            if not isinstance(attempt[field], str):
                raise BackupError("invalid attempt field", reason="metadata-invalid")
        if attempt["result"] == "failed" and (
                attempt["stage"] not in HEALTH_FAILURE_STAGES
                or attempt["error_type"] != "BackupError"
                or attempt["message"] != HEALTH_FAILURE_MESSAGE):
            raise BackupError("unrecognized persistent failure diagnostics", reason="metadata-invalid")
    retention = state["last_retention"]
    if retention is not None:
        checked_object(retention, ("completed_at", "result", "deleted"))
        checked_time(retention["completed_at"])
        if retention["result"] not in ("success", "failed") or not isinstance(retention["deleted"], list):
            raise BackupError("invalid retention health", reason="metadata-invalid")
        for name in retention["deleted"]:
            if not isinstance(name, str):
                raise BackupError("invalid retention name", reason="metadata-invalid")
            checked_snapshot_path(str(snapshot_root / name), snapshot_root)


def secure_state_directory(directory, create=False):
    if not os.path.lexists(directory):
        if not create:
            return False
        directory.mkdir(mode=0o700, parents=False)
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
        raise BackupError("state directory must be an owned real directory", reason="metadata-invalid")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise BackupError("state directory must have mode 0700", reason="metadata-invalid")
    return True


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BackupError("duplicate persistent JSON key", reason="metadata-invalid")
        result[key] = value
    return result


def load_json(path, default):
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return default
    except OSError as exc:
        raise BackupError("cannot open persistent metadata", reason="metadata-invalid") from exc
    with os.fdopen(descriptor, "r") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise BackupError("metadata must be an owned mode 0600 regular file", reason="metadata-invalid")
        try:
            return json.load(stream, object_pairs_hook=reject_duplicate_keys)
        except (ValueError, UnicodeError) as exc:
            raise BackupError("malformed persistent JSON", reason="metadata-invalid") from exc


def atomic_json(path, value):
    if not secure_state_directory(path.parent):
        raise BackupError("state directory is absent", reason="metadata-invalid")
    if os.path.lexists(path):
        load_json(path, None)
    descriptor, temporary = tempfile.mkstemp(prefix=".minecraft-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.lexists(temporary):
            os.unlink(temporary)


def load_metadata(directory=STATE_DIRECTORY, snapshot_root=SNAPSHOT_ROOT, create=False):
    exists = secure_state_directory(directory, create=create)
    state = {"schema_version": 2, "pending_snapshot": None, "pending_deletion": None, "last_attempt": None,
             "last_success": None, "last_retention": None}
    manifest = {"schema_version": 2, "snapshots": []}
    if exists:
        if (os.path.lexists(directory / "managed-snapshots.json")
                and not os.path.lexists(directory / "state.json")):
            raise BackupError("state file is missing beside an established manifest", reason="metadata-invalid")
        state = load_json(directory / "state.json", state)
        manifest = load_json(directory / "managed-snapshots.json", manifest)
    validate_metadata(state, manifest, snapshot_root)
    if state["last_success"] is not None and not os.path.lexists(directory / "managed-snapshots.json"):
        raise BackupError("managed manifest is missing after a successful snapshot", reason="metadata-invalid")
    return state, manifest


def verify_snapshot_root(snapshot_root, mount_checker):
    info = snapshot_root.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
            or stat.S_IMODE(info.st_mode) != 0o700 or mount_checker(snapshot_root)):
        raise BackupError("snapshot root must be an owned unmounted mode 0700 directory")


def verify_snapshot_identity(path, filesystem_uuid, snapshot_root=SNAPSHOT_ROOT,
                             runner=subprocess.run, mount_checker=is_mountpoint):
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


def register_pending(state, manifest, directory, snapshot_root, runner, mount_checker):
    pending = state["pending_snapshot"]
    if pending is None:
        return
    verify_snapshot_root(snapshot_root, mount_checker)
    path = checked_snapshot_path(pending["path"], snapshot_root)
    existing = next((record for record in manifest["snapshots"] if record["path"] == str(path)), None)
    if not os.path.lexists(path):
        if existing is not None:
            raise BackupError("registered pending snapshot is missing")
        state["pending_snapshot"] = None
        state["last_attempt"] = {"started_at": pending["planned_at"], "finished_at": utc_now(), "result": "aborted"}
        atomic_json(directory / "state.json", state)
        return
    identity = verify_snapshot_identity(path, pending["source_filesystem_uuid"], snapshot_root, runner, mount_checker)
    record = {"name": path.name, "path": str(path), "created_at": pending["planned_at"],
              "filesystem_uuid": pending["source_filesystem_uuid"], "subvolume_uuid": identity}
    if existing is not None and existing != record:
        raise BackupError("pending snapshot manifest identity mismatch")
    if existing is None:
        manifest["snapshots"].append(record)
        validate_metadata(state, manifest, snapshot_root)
        atomic_json(directory / "managed-snapshots.json", manifest)
    state["last_success"] = {"created_at": record["created_at"], "snapshot_path": str(path),
                             "snapshot_uuid": identity, "filesystem_uuid": record["filesystem_uuid"]}
    state["pending_snapshot"] = None
    state["last_attempt"] = {"started_at": pending["planned_at"], "finished_at": utc_now(), "result": "recovered"}
    atomic_json(directory / "state.json", state)


def reconcile_deletion(state, manifest, directory, snapshot_root, runner, mount_checker, deleted):
    record = state["pending_deletion"]
    if record is None:
        return
    validate_metadata(state, manifest, snapshot_root)
    verify_snapshot_root(snapshot_root, mount_checker)
    path = checked_snapshot_path(record["path"], snapshot_root)
    if btrfs_filesystem_uuid(snapshot_root, runner=runner) != record["filesystem_uuid"]:
        raise BackupError("deletion intent filesystem is not mounted")
    existing = next((r for r in manifest["snapshots"] if r["path"] == str(path)), None)
    if os.path.lexists(path):
        # A manifest write completed before intent clearing cannot authorize a
        # replacement object. Only an unchanged owned object may be retried.
        if existing is None:
            raise BackupError("object exists after deletion ownership was removed")
        identity = verify_snapshot_identity(path, record["filesystem_uuid"], snapshot_root, runner, mount_checker)
        if identity != record["subvolume_uuid"]:
            raise BackupError("retention subvolume UUID mismatch", reason="snapshot-identity-mismatch")
        run_btrfs_preflight(["btrfs", "subvolume", "delete", "--commit-after", str(path)],
                           runner=runner, timeout=DEFAULT_SNAPSHOT_TIMEOUT)
        if os.path.lexists(path):
            raise BackupError("retention deletion did not remove snapshot path")
    deleted.append(path.name)
    if existing is not None:
        manifest["snapshots"].remove(existing)
        atomic_json(directory / "managed-snapshots.json", manifest)
    state["pending_deletion"] = None
    atomic_json(directory / "state.json", state)


def apply_retention(state, manifest, directory=STATE_DIRECTORY,
                    snapshot_root=SNAPSHOT_ROOT, runner=subprocess.run,
                    mount_checker=is_mountpoint, keep=KEEP_SNAPSHOTS,
                    deletion_budget=MAX_RETENTION_DELETIONS_PER_RUN):
    validate_metadata(state, manifest, snapshot_root)
    if type(keep) is not int or keep < 1:
        raise BackupError("retention count must be a positive integer")
    if type(deletion_budget) is not int or deletion_budget < 0:
        raise BackupError("retention deletion budget must be a nonnegative integer")
    deleted = []
    protected = set()
    if state["last_success"] is not None:
        protected.add(state["last_success"]["snapshot_path"])
    if state["pending_snapshot"] is not None:
        protected.add(state["pending_snapshot"]["path"])
    try:
        verify_snapshot_root(snapshot_root, mount_checker)
        intent = state["pending_deletion"]
        for record in manifest["snapshots"]:
            if not os.path.lexists(record["path"]) and record != intent:
                raise BackupError("managed snapshot disappeared without deletion intent")
        if deletion_budget and state["pending_deletion"] is not None:
            reconcile_deletion(state, manifest, directory, snapshot_root, runner, mount_checker, deleted)
        ordered = sorted(manifest["snapshots"], key=lambda entry: (entry["created_at"], entry["path"]))
        candidates = [record for record in ordered[:-keep] if record["path"] not in protected]
        candidates = candidates[:max(0, deletion_budget - len(deleted))]
        for record in candidates:
            state["pending_deletion"] = dict(record)
            atomic_json(directory / "state.json", state)
            reconcile_deletion(state, manifest, directory, snapshot_root, runner, mount_checker, deleted)
        state["last_retention"] = {"completed_at": utc_now(), "result": "success", "deleted": deleted}
        atomic_json(directory / "state.json", state)
        return len(deleted)
    except Exception as exc:
        # Only health changes here; never overwrite a stale ownership manifest
        # after a failed manifest replacement or directory fsync.
        durable, _ = load_metadata(directory, snapshot_root)
        durable["last_retention"] = {"completed_at": utc_now(), "result": "failed", "deleted": deleted}
        atomic_json(directory / "state.json", durable)
        raise BackupError("retention failed") from exc


def sync_snapshot_filesystem(snapshot_mount, runner=subprocess.run):
    started = time.monotonic()
    runner(["btrfs", "filesystem", "sync", str(snapshot_mount)],
           check=True, capture_output=True, text=True,
           timeout=DEFAULT_SNAPSHOT_TIMEOUT)
    print(f"snapshot filesystem sync completed in {time.monotonic() - started:.3f} seconds", flush=True)


def perform_managed_backup(directory=STATE_DIRECTORY, source=SOURCE_SUBVOLUME,
                           snapshot_mount=SNAPSHOT_MOUNT, snapshot_root=SNAPSHOT_ROOT,
                           runner=subprocess.run, mount_checker=is_mountpoint,
                           recovery_marker=AUTOSAVE_RECOVERY_MARKER,
                           connection_factory=msmp.open_connection, now=None):
    recover_abandoned_autosave(marker=recovery_marker, connection_factory=connection_factory)
    state, manifest = load_metadata(directory, snapshot_root, create=True)
    started = utc_now()
    stage = "environment-preflight"
    try:
        for path in (source, snapshot_mount):
            if path.is_symlink() or not path.is_dir() or not mount_checker(path):
                raise BackupError("required backup mount is absent or invalid", reason="mount-missing")
        expected_uuid = btrfs_filesystem_uuid(source, runner=runner)
        if btrfs_filesystem_uuid(snapshot_mount, runner=runner) != expected_uuid:
            raise BackupError("backup filesystem UUID mismatch", reason="filesystem-mismatch")
        if state["pending_snapshot"] is not None and state["pending_snapshot"]["source_filesystem_uuid"] != expected_uuid:
            raise BackupError("pending source filesystem UUID mismatch", reason="filesystem-mismatch")
        if state["pending_snapshot"] is not None and Path(state["pending_snapshot"]["path"]).exists():
            stage = "durability-sync"
            sync_snapshot_filesystem(snapshot_mount, runner)
        stage = "reconciliation"
        register_pending(state, manifest, directory, snapshot_root, runner, mount_checker)
        deletion_budget = MAX_RETENTION_DELETIONS_PER_RUN
        if state["pending_deletion"] is not None:
            deletion_budget -= apply_retention(state, manifest, directory, snapshot_root, runner, mount_checker,
                                               deletion_budget=1)
        stage = "preflight"
        plan = prepare_snapshot(source, snapshot_mount, snapshot_root, now, runner, mount_checker)
        stage = "readiness"
        wait_for_management(connection_factory)
        state["pending_snapshot"] = {"path": str(plan.destination), "planned_at": started,
                                     "source_filesystem_uuid": expected_uuid}
        stage = "pending-state"
        atomic_json(directory / "state.json", state)
        stage = "consistency-transaction"
        perform_backup(action=lambda: create_readonly_snapshot(plan, runner=runner),
                       connection_factory=connection_factory, recovery_marker=recovery_marker)
        stage = "durability-sync"
        sync_snapshot_filesystem(snapshot_mount, runner)
        stage = "registration"
        register_pending(state, manifest, directory, snapshot_root, runner, mount_checker)
        state["last_attempt"] = {"started_at": started, "finished_at": utc_now(), "result": "success"}
        atomic_json(directory / "state.json", state)
        stage = "retention"
        apply_retention(state, manifest, directory, snapshot_root, runner, mount_checker,
                        deletion_budget=deletion_budget)
        return plan.destination
    except Exception as exc:
        # Reload durable state: failure after replace may already have published it.
        # Transport and peer error text must never be copied into health metadata.
        durable, _ = load_metadata(directory, snapshot_root)
        durable["last_attempt"] = {"started_at": started, "finished_at": utc_now(), "result": "failed",
                                   "stage": stage, "error_type": "BackupError",
                                   "message": HEALTH_FAILURE_MESSAGE}
        atomic_json(directory / "state.json", durable)
        raise BackupError("managed backup failed at " + stage,
                          reason=diagnostic_reason(exc, stage), stage=stage) from exc


def wait_for_management(connection_factory=msmp.open_connection, timeout=90.0,
                        clock=time.monotonic, sleeper=time.sleep):
    deadline = clock() + timeout
    while clock() < deadline:
        try:
            with connection_factory() as websocket:
                session = msmp.MsmpSession(websocket)
                session.require_backup_capabilities(
                    timeout=min(DEFAULT_RPC_TIMEOUT, max(0.001, deadline - clock())),
                    additional_capabilities=("minecraft:server/status",),
                )
                remaining = deadline - clock()
                if remaining <= 0:
                    raise TimeoutError("management readiness deadline expired")
                status = session.call("minecraft:server/status", timeout=min(DEFAULT_RPC_TIMEOUT, remaining))
                if not isinstance(status, dict) or type(status.get("started")) is not bool:
                    raise msmp.ProtocolError("server status has no boolean initialization state")
                if status["started"]:
                    return
            remaining = deadline - clock()
            if remaining > 0:
                sleeper(min(1.0, remaining))
        except (OSError, TimeoutError, ConnectionClosed, msmp.RpcError) as exc:
            if isinstance(exc, msmp.RpcError) and exc.error != {
                "code": -32600,
                "message": "Invalid Request",
                "data": "Method cannot be dispatched pre server initialization: minecraft:server/status",
            }:
                raise
            remaining = deadline - clock()
            if remaining <= 0:
                break
            sleeper(min(1.0, remaining))
    raise BackupError("management readiness timed out", reason="management-unavailable")


def status_report(state, manifest, now=None, recovery_marker=AUTOSAVE_RECOVERY_MARKER):
    now = now or datetime.now(timezone.utc)
    problems = []
    success = state["last_success"]
    protected = {success["snapshot_path"]} if success else set()
    if state["pending_snapshot"] is not None:
        protected.add(state["pending_snapshot"]["path"])
    ordered = sorted(manifest["snapshots"], key=lambda entry: (entry["created_at"], entry["path"]))
    backlog = sum(record["path"] not in protected for record in ordered[:-KEEP_SNAPSHOTS])
    if backlog:
        problems.append("retention-backlog")
    age = None
    if success is not None:
        age = (now - datetime.strptime(success["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds()
        if age < 0:
            problems.append("success-time-in-future")
        elif age > 13 * 3600:
            problems.append("success-overdue")
        matching = [r for r in manifest["snapshots"] if r["path"] == success["snapshot_path"]
                    and r["subvolume_uuid"] == success["snapshot_uuid"]
                    and r["filesystem_uuid"] == success["filesystem_uuid"]
                    and r["created_at"] == success["created_at"]]
        if not matching:
            problems.append("last-success-not-owned")
        if not manifest["snapshots"]:
            problems.append("established-manifest-empty")
    elif state["last_attempt"] is not None or manifest["snapshots"]:
        problems.append("no-successful-snapshot")
    for field in ("pending_snapshot", "pending_deletion"):
        if state[field] is not None:
            problems.append(field.replace("_", "-"))
    if os.path.lexists(recovery_marker):
        problems.append("autosave-recovery-required")
    if state["last_attempt"] is not None and state["last_attempt"]["result"] == "failed":
        problems.append("last-attempt-failed")
    if state["last_retention"] is not None and state["last_retention"]["result"] == "failed":
        problems.append("retention-failed")
    return {"health": "attention" if problems else ("ok" if success else "uninitialized"),
            "problems": problems, "last_success_age_seconds": age,
            "expected_interval_seconds": 21600, "overdue_after_seconds": 46800,
            "managed_snapshot_count": len(manifest["snapshots"]),
            "retention_backlog_count": backlog, "state": state}


def live_status_report(state, manifest, source=SOURCE_SUBVOLUME,
                       snapshot_mount=SNAPSHOT_MOUNT, snapshot_root=SNAPSHOT_ROOT,
                       runner=subprocess.run, mount_checker=is_mountpoint):
    report = status_report(state, manifest)
    try:
        for path in (source, snapshot_mount):
            if path.is_symlink() or not path.is_dir() or not mount_checker(path):
                raise BackupError("required backup mount is absent or invalid", reason="mount-missing")
        verify_source_completeness(source, runner=runner)
        expected_uuid = btrfs_filesystem_uuid(source, runner=runner)
        if btrfs_filesystem_uuid(snapshot_mount, runner=runner) != expected_uuid:
            raise BackupError("backup filesystem UUID mismatch", reason="filesystem-mismatch")
        success = state["last_success"]
        if success is None or success["filesystem_uuid"] != expected_uuid:
            raise BackupError("no matching successful recovery point")
        path = checked_snapshot_path(success["snapshot_path"], snapshot_root)
        identity = verify_snapshot_identity(path, expected_uuid, snapshot_root, runner, mount_checker)
        if identity != success["snapshot_uuid"]:
            raise BackupError("last success subvolume UUID mismatch", reason="snapshot-identity-mismatch")
        for record in manifest["snapshots"]:
            if record["filesystem_uuid"] != expected_uuid:
                raise BackupError("managed snapshot filesystem mismatch", reason="filesystem-mismatch")
            path = checked_snapshot_path(record["path"], snapshot_root)
            identity = verify_snapshot_identity(path, expected_uuid, snapshot_root, runner, mount_checker)
            if identity != record["subvolume_uuid"]:
                raise BackupError("managed snapshot identity mismatch", reason="snapshot-identity-mismatch")
    except Exception:
        report["problems"].append("live-snapshot-verification-failed")
        report["health"] = "attention"
        report["live_verification"] = "failed"
    else:
        report["live_verification"] = "passed"
    return report


def command_status(live=False):
    state, manifest = load_metadata()
    report = live_status_report(state, manifest) if live else status_report(state, manifest)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 1 if report["problems"] else 0


def require_root() -> None:
    if os.geteuid() != 0:
        raise BackupError(
            "must run as root"
        )


def command_backup() -> None:
    require_root()

    with exclusive_backup_lock():
        snapshot = perform_managed_backup()

    print(
        f"created read-only Minecraft snapshot: {snapshot}"
    )


def command_recover_autosave() -> None:
    require_root()

    with exclusive_backup_lock():
        recovered = recover_abandoned_autosave()

    if recovered:
        print(
            "recovered Minecraft autosave from abandoned backup"
        )


def main() -> int:
    try:
        if len(sys.argv) == 1:
            command_backup()
        elif sys.argv[1:] == ["status"]:
            return command_status()
        elif sys.argv[1:] == ["status", "--live"]:
            return command_status(live=True)
        elif sys.argv[1:] in (["--help"], ["-h"]):
            print("usage: minecraft-backup [status [--live]|recover-autosave]")
        elif sys.argv[1:] == ["recover-autosave"]:
            command_recover_autosave()
        else:
            raise BackupError(
                "usage: minecraft-backup [status [--live]|recover-autosave]"
            )

    except Exception as exc:
        stage = exc.stage if isinstance(exc, BackupError) and exc.stage in HEALTH_FAILURE_STAGES else "operation"
        print(
            f"minecraft-backup: failed stage={stage} reason={diagnostic_reason(exc, stage)}; inspect status and service journal",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
