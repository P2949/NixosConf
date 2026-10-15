from . import btrfs, metadata
from .errors import BackupError, HEALTH_FAILURE_STAGES, HEALTH_FAILURE_MESSAGE, DIAGNOSTIC_REASONS
#!/usr/bin/env python3

import argparse
import fcntl
import json
import stat
import tempfile
import time
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from functools import partial
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from websockets.exceptions import ConnectionClosed


from minecraft_tools.config import MinecraftConfig, load_config

MAX_RETENTION_DELETIONS_PER_RUN = 4








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


from minecraft_tools import msmp


DEFAULT_RPC_TIMEOUT = msmp.DEFAULT_RPC_TIMEOUT
DEFAULT_SAVE_TIMEOUT = msmp.DEFAULT_SAVE_TIMEOUT








@contextmanager
def exclusive_backup_lock(
    path: Path = None,
):
    if path is None:
        raise BackupError("explicit lock path is required")
    prepare_recovery_directory(path.parent)
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
    directory: Path = None,
) -> None:
    if directory is None:
        raise BackupError("explicit deployment policy values are required")
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
    marker: Path = None,
) -> None:
    if marker is None:
        raise BackupError("explicit deployment policy values are required")
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
    marker: Path = None,
) -> bool:
    if marker is None:
        raise BackupError("explicit deployment policy values are required")
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
    marker: Path = None,
) -> None:
    if marker is None:
        raise BackupError("explicit deployment policy values are required")
    try:
        marker.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise BackupError(
            f"cannot remove autosave recovery marker {marker}: {exc}"
        ) from exc
















def restore_autosave_with_fresh_connection(
    connection_factory=None,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
) -> None:
    if connection_factory is None:
        raise BackupError("explicit management connection is required")
    with connection_factory() as websocket:
        recovery_session = msmp.MsmpSession(websocket)
        recovery_session.set_autosave(
            True,
            timeout=rpc_timeout,
        )


def recover_abandoned_autosave(
    marker: Path = None,
    connection_factory=None,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
) -> bool:
    if connection_factory is None:
        raise BackupError("explicit management connection is required")
    if marker is None:
        raise BackupError("explicit deployment policy values are required")
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
    action=btrfs.create_readonly_snapshot,
    connection_factory=None,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
    save_timeout: float = DEFAULT_SAVE_TIMEOUT,
    recovery_marker: Path = None,
):
    if connection_factory is None:
        raise BackupError("explicit management connection is required")
    if recovery_marker is None:
        raise BackupError("explicit deployment policy values are required")
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
    source: Path = None,
    snapshot_mount: Path = None,
    snapshot_root: Path = None,
    now: datetime | None = None,
    mount_checker=btrfs.is_mountpoint,
    preflight_runner=subprocess.run,
    snapshot_runner=subprocess.run,
    preflight_timeout: float = btrfs.DEFAULT_PREFLIGHT_TIMEOUT,
    snapshot_timeout: float = btrfs.DEFAULT_SNAPSHOT_TIMEOUT,
    connection_factory=None,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
    save_timeout: float = DEFAULT_SAVE_TIMEOUT,
    recovery_marker: Path = None,
):
    if connection_factory is None:
        raise BackupError("explicit management connection is required")
    if source is None or snapshot_mount is None or snapshot_root is None or recovery_marker is None:
        raise BackupError("explicit deployment policy values are required")
    recover_abandoned_autosave(
        marker=recovery_marker,
        connection_factory=connection_factory,
        rpc_timeout=rpc_timeout,
    )

    plan = btrfs.prepare_snapshot(
        source=source,
        snapshot_mount=snapshot_mount,
        snapshot_root=snapshot_root,
        now=now,
        runner=preflight_runner,
        mount_checker=mount_checker,
        timeout=preflight_timeout,
    )

    return perform_backup(
        action=lambda: btrfs.create_readonly_snapshot(
            plan,
            runner=snapshot_runner,
            timeout=snapshot_timeout,
        ),
        connection_factory=connection_factory,
        rpc_timeout=rpc_timeout,
        save_timeout=save_timeout,
        recovery_marker=recovery_marker,
    )






























def register_pending(state, manifest, directory, snapshot_root, runner, mount_checker):
    pending = state["pending_snapshot"]
    if pending is None:
        return
    btrfs.verify_snapshot_root(snapshot_root, mount_checker)
    path = metadata.checked_snapshot_path(pending["path"], snapshot_root)
    existing = next((record for record in manifest["snapshots"] if record["path"] == str(path)), None)
    if not os.path.lexists(path):
        if existing is not None:
            raise BackupError("registered pending snapshot is missing")
        state["pending_snapshot"] = None
        state["last_attempt"] = {"started_at": pending["planned_at"], "finished_at": metadata.utc_now(), "result": "aborted"}
        metadata.atomic_json(directory / "state.json", state)
        return
    identity = btrfs.verify_snapshot_identity(path, pending["source_filesystem_uuid"], snapshot_root, runner, mount_checker)
    record = {"name": path.name, "path": str(path), "created_at": pending["planned_at"],
              "filesystem_uuid": pending["source_filesystem_uuid"], "subvolume_uuid": identity}
    if existing is not None and existing != record:
        raise BackupError("pending snapshot manifest identity mismatch")
    if existing is None:
        manifest["snapshots"].append(record)
        metadata.validate_metadata(state, manifest, snapshot_root)
        metadata.atomic_json(directory / "managed-snapshots.json", manifest)
    state["last_success"] = {"created_at": record["created_at"], "snapshot_path": str(path),
                             "snapshot_uuid": identity, "filesystem_uuid": record["filesystem_uuid"]}
    state["pending_snapshot"] = None
    state["last_attempt"] = {"started_at": pending["planned_at"], "finished_at": metadata.utc_now(), "result": "recovered"}
    metadata.atomic_json(directory / "state.json", state)


def reconcile_deletion(state, manifest, directory, snapshot_root, runner, mount_checker, deleted):
    record = state["pending_deletion"]
    if record is None:
        return
    metadata.validate_metadata(state, manifest, snapshot_root)
    btrfs.verify_snapshot_root(snapshot_root, mount_checker)
    path = metadata.checked_snapshot_path(record["path"], snapshot_root)
    if btrfs.btrfs_filesystem_uuid(snapshot_root, runner=runner) != record["filesystem_uuid"]:
        raise BackupError("deletion intent filesystem is not mounted")
    existing = next((r for r in manifest["snapshots"] if r["path"] == str(path)), None)
    if os.path.lexists(path):
        # A manifest write completed before intent clearing cannot authorize a
        # replacement object. Only an unchanged owned object may be retried.
        if existing is None:
            raise BackupError("object exists after deletion ownership was removed")
        identity = btrfs.verify_snapshot_identity(path, record["filesystem_uuid"], snapshot_root, runner, mount_checker)
        if identity != record["subvolume_uuid"]:
            raise BackupError("retention subvolume UUID mismatch", reason="snapshot-identity-mismatch")
        btrfs.run_btrfs_preflight(["btrfs", "subvolume", "delete", "--commit-after", str(path)],
                           runner=runner, timeout=btrfs.DEFAULT_SNAPSHOT_TIMEOUT)
        if os.path.lexists(path):
            raise BackupError("retention deletion did not remove snapshot path")
    deleted.append(path.name)
    if existing is not None:
        manifest["snapshots"].remove(existing)
        metadata.atomic_json(directory / "managed-snapshots.json", manifest)
    state["pending_deletion"] = None
    metadata.atomic_json(directory / "state.json", state)


def apply_retention(state, manifest, directory=None,
                    snapshot_root=None, runner=subprocess.run,
                    mount_checker=btrfs.is_mountpoint, keep=None,
                    deletion_budget=MAX_RETENTION_DELETIONS_PER_RUN):
    if directory is None or snapshot_root is None or keep is None:
        raise BackupError("explicit deployment policy values are required")
    metadata.validate_metadata(state, manifest, snapshot_root)
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
        btrfs.verify_snapshot_root(snapshot_root, mount_checker)
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
            metadata.atomic_json(directory / "state.json", state)
            reconcile_deletion(state, manifest, directory, snapshot_root, runner, mount_checker, deleted)
        state["last_retention"] = {"completed_at": metadata.utc_now(), "result": "success", "deleted": deleted}
        metadata.atomic_json(directory / "state.json", state)
        return len(deleted)
    except Exception as exc:
        # Only health changes here; never overwrite a stale ownership manifest
        # after a failed manifest replacement or directory fsync.
        durable, _ = metadata.load_metadata(directory, snapshot_root)
        durable["last_retention"] = {"completed_at": metadata.utc_now(), "result": "failed", "deleted": deleted}
        metadata.atomic_json(directory / "state.json", durable)
        raise BackupError("retention failed") from exc




def perform_managed_backup(directory=None, source=None,
                           snapshot_mount=None, snapshot_root=None,
                           runner=subprocess.run, mount_checker=btrfs.is_mountpoint,
                           recovery_marker=None,
                           connection_factory=None, now=None, keep=None):
    if connection_factory is None:
        raise BackupError("explicit management connection is required")
    if directory is None or source is None or snapshot_mount is None or snapshot_root is None or recovery_marker is None:
        raise BackupError("explicit deployment policy values are required")
    if type(keep) is not int or keep < 1:
        raise BackupError("retention count must be a positive integer")
    recover_abandoned_autosave(marker=recovery_marker, connection_factory=connection_factory)
    state, manifest = metadata.load_metadata(directory, snapshot_root, create=True)
    started = metadata.utc_now()
    stage = "environment-preflight"
    try:
        for path in (source, snapshot_mount):
            if path.is_symlink() or not path.is_dir() or not mount_checker(path):
                raise BackupError("required backup mount is absent or invalid", reason="mount-missing")
        expected_uuid = btrfs.btrfs_filesystem_uuid(source, runner=runner)
        if btrfs.btrfs_filesystem_uuid(snapshot_mount, runner=runner) != expected_uuid:
            raise BackupError("backup filesystem UUID mismatch", reason="filesystem-mismatch")
        if state["pending_snapshot"] is not None and state["pending_snapshot"]["source_filesystem_uuid"] != expected_uuid:
            raise BackupError("pending source filesystem UUID mismatch", reason="filesystem-mismatch")
        if state["pending_snapshot"] is not None and Path(state["pending_snapshot"]["path"]).exists():
            stage = "durability-sync"
            btrfs.sync_snapshot_filesystem(snapshot_mount, runner)
        stage = "reconciliation"
        register_pending(state, manifest, directory, snapshot_root, runner, mount_checker)
        deletion_budget = MAX_RETENTION_DELETIONS_PER_RUN
        if state["pending_deletion"] is not None:
            deletion_budget -= apply_retention(state, manifest, directory, snapshot_root, runner, mount_checker,
                                               deletion_budget=1, keep=keep)
        stage = "preflight"
        plan = btrfs.prepare_snapshot(source, snapshot_mount, snapshot_root, now, runner, mount_checker)
        stage = "readiness"
        wait_for_management(connection_factory)
        state["pending_snapshot"] = {"path": str(plan.destination), "planned_at": started,
                                     "source_filesystem_uuid": expected_uuid}
        stage = "pending-state"
        metadata.atomic_json(directory / "state.json", state)
        stage = "consistency-transaction"
        perform_backup(action=lambda: btrfs.create_readonly_snapshot(plan, runner=runner),
                       connection_factory=connection_factory, recovery_marker=recovery_marker)
        stage = "durability-sync"
        btrfs.sync_snapshot_filesystem(snapshot_mount, runner)
        stage = "registration"
        register_pending(state, manifest, directory, snapshot_root, runner, mount_checker)
        state["last_attempt"] = {"started_at": started, "finished_at": metadata.utc_now(), "result": "success"}
        metadata.atomic_json(directory / "state.json", state)
        stage = "retention"
        apply_retention(state, manifest, directory, snapshot_root, runner, mount_checker,
                        deletion_budget=deletion_budget, keep=keep)
        return plan.destination
    except Exception as exc:
        # Reload durable state: failure after replace may already have published it.
        # Transport and peer error text must never be copied into health metadata.
        durable, _ = metadata.load_metadata(directory, snapshot_root)
        durable["last_attempt"] = {"started_at": started, "finished_at": metadata.utc_now(), "result": "failed",
                                   "stage": stage, "error_type": "BackupError",
                                   "message": HEALTH_FAILURE_MESSAGE}
        metadata.atomic_json(directory / "state.json", durable)
        raise BackupError("managed backup failed at " + stage,
                          reason=diagnostic_reason(exc, stage), stage=stage) from exc


def wait_for_management(connection_factory=None, timeout=90.0,
                        clock=time.monotonic, sleeper=time.sleep):
    if connection_factory is None:
        raise BackupError("explicit management connection is required")
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


def status_report(state, manifest, now=None, recovery_marker=None, keep=None):
    if type(keep) is not int or keep < 1:
        raise BackupError("retention count must be a positive integer")
    if recovery_marker is None:
        raise BackupError("explicit deployment policy values are required")
    now = now or datetime.now(timezone.utc)
    problems = []
    success = state["last_success"]
    protected = {success["snapshot_path"]} if success else set()
    if state["pending_snapshot"] is not None:
        protected.add(state["pending_snapshot"]["path"])
    ordered = sorted(manifest["snapshots"], key=lambda entry: (entry["created_at"], entry["path"]))
    backlog = sum(record["path"] not in protected for record in ordered[:-keep])
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


def live_status_report(state, manifest, source=None,
                       snapshot_mount=None, snapshot_root=None,
                       runner=subprocess.run, mount_checker=btrfs.is_mountpoint, recovery_marker=None, keep=None):
    if source is None or snapshot_mount is None or snapshot_root is None:
        raise BackupError("explicit deployment policy values are required")
    report = status_report(state, manifest, recovery_marker=recovery_marker, keep=keep)
    try:
        for path in (source, snapshot_mount):
            if path.is_symlink() or not path.is_dir() or not mount_checker(path):
                raise BackupError("required backup mount is absent or invalid", reason="mount-missing")
        btrfs.verify_source_completeness(source, runner=runner)
        expected_uuid = btrfs.btrfs_filesystem_uuid(source, runner=runner)
        if btrfs.btrfs_filesystem_uuid(snapshot_mount, runner=runner) != expected_uuid:
            raise BackupError("backup filesystem UUID mismatch", reason="filesystem-mismatch")
        success = state["last_success"]
        if success is None or success["filesystem_uuid"] != expected_uuid:
            raise BackupError("no matching successful recovery point")
        path = metadata.checked_snapshot_path(success["snapshot_path"], snapshot_root)
        identity = btrfs.verify_snapshot_identity(path, expected_uuid, snapshot_root, runner, mount_checker)
        if identity != success["snapshot_uuid"]:
            raise BackupError("last success subvolume UUID mismatch", reason="snapshot-identity-mismatch")
        for record in manifest["snapshots"]:
            if record["filesystem_uuid"] != expected_uuid:
                raise BackupError("managed snapshot filesystem mismatch", reason="filesystem-mismatch")
            path = metadata.checked_snapshot_path(record["path"], snapshot_root)
            identity = btrfs.verify_snapshot_identity(path, expected_uuid, snapshot_root, runner, mount_checker)
            if identity != record["subvolume_uuid"]:
                raise BackupError("managed snapshot identity mismatch", reason="snapshot-identity-mismatch")
    except Exception:
        report["problems"].append("live-snapshot-verification-failed")
        report["health"] = "attention"
        report["live_verification"] = "failed"
    else:
        report["live_verification"] = "passed"
    return report


def command_status(config: MinecraftConfig, live=False):
    state, manifest = metadata.load_metadata(config.state_directory, config.snapshot_root)
    options = dict(recovery_marker=config.runtime_directory / "autosave-needs-restore", keep=config.keep_snapshots)
    report = live_status_report(state, manifest, source=config.source, snapshot_mount=config.snapshot_mount,
                               snapshot_root=config.snapshot_root, **options) if live else status_report(state, manifest, **options)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 1 if report["problems"] else 0


def require_root() -> None:
    if os.geteuid() != 0:
        raise BackupError(
            "must run as root"
        )


def command_backup(config: MinecraftConfig) -> None:
    require_root()

    with exclusive_backup_lock(config.runtime_directory / "backup.lock"):
        snapshot = perform_managed_backup(directory=config.state_directory, source=config.source,
            snapshot_mount=config.snapshot_mount, snapshot_root=config.snapshot_root,
            recovery_marker=config.runtime_directory / "autosave-needs-restore",
            connection_factory=partial(msmp.open_connection, config), keep=config.keep_snapshots)

    print(
        f"created read-only Minecraft snapshot: {snapshot}"
    )


def command_recover_autosave(config: MinecraftConfig) -> None:
    require_root()

    with exclusive_backup_lock(config.runtime_directory / "backup.lock"):
        recovered = recover_abandoned_autosave(marker=config.runtime_directory / "autosave-needs-restore",
            connection_factory=partial(msmp.open_connection, config))

    if recovered:
        print(
            "recovered Minecraft autosave from abandoned backup"
        )


def main() -> int:
    parser = argparse.ArgumentParser(usage="minecraft-backup --config FILE [status [--live]|recover-autosave]")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("command", nargs="?", choices=("status", "recover-autosave"), default=None)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.live and args.command != "status":
        parser.error("--live requires status")
    try:
        config = load_config(args.config)
        if args.command == "status":
            return command_status(config, live=args.live)
        if args.command == "recover-autosave":
            command_recover_autosave(config)
        else:
            command_backup(config)

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
