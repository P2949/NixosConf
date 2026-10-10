#!/usr/bin/env python3

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from collections import deque
from datetime import datetime, timezone
from pathlib import Path


SOURCE = Path(os.environ["MINECRAFT_BACKUP_SOURCE"])

SPEC = importlib.util.spec_from_file_location(
    "minecraft_backup",
    SOURCE,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SOURCE}")

backup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup)


def response(request_id, result):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def notification(method):
    return {
        "jsonrpc": "2.0",
        "method": method,
    }


def discovery():
    return {
        "openrpc": "1.3.2",
        "methods": [
            {"name": name}
            for name in sorted(
                backup.msmp.BACKUP_CAPABILITIES | {"minecraft:server/status"}
            )
        ],
    }


class FakeWebSocket:
    def __init__(self, incoming):
        self.incoming = deque(incoming)
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def send(self, raw):
        self.sent.append(json.loads(raw))

    def recv(self, timeout=None):
        del timeout

        if not self.incoming:
            raise TimeoutError("fake websocket timed out")

        return json.dumps(self.incoming.popleft())


class ConnectionFactory:
    def __init__(self, *websockets):
        self.websockets = deque(websockets)
        self.calls = 0

    def __call__(self):
        self.calls += 1

        if not self.websockets:
            raise RuntimeError("unexpected connection attempt")

        return self.websockets.popleft()


class FakePreflightRunner:
    DEFAULT_UUID = "11111111-1111-1111-1111-111111111111"
    OTHER_UUID = "22222222-2222-2222-2222-222222222222"

    def __init__(
        self,
        source,
        snapshot_mount,
        source_uuid=DEFAULT_UUID,
        snapshot_uuid=None,
        fail_subvolume=False,
    ):
        self.source = source
        self.snapshot_mount = snapshot_mount
        self.source_uuid = source_uuid
        self.snapshot_uuid = (
            source_uuid
            if snapshot_uuid is None
            else snapshot_uuid
        )
        self.fail_subvolume = fail_subvolume
        self.calls = []

    def __call__(
        self,
        arguments,
        *,
        check,
        capture_output,
        text,
        timeout,
    ):
        arguments = list(arguments)
        self.calls.append(arguments)

        if not check or not capture_output or not text:
            raise AssertionError(
                "preflight commands must capture text output and fail closed"
            )

        if timeout != backup.DEFAULT_PREFLIGHT_TIMEOUT:
            raise AssertionError(
                f"unexpected preflight timeout: {timeout}"
            )

        if arguments[:4] == ["btrfs", "subvolume", "list", "-o"]:
            return subprocess.CompletedProcess(arguments, 0, stdout="", stderr="")

        if arguments[:3] == [
            "btrfs",
            "subvolume",
            "show",
        ]:
            if Path(arguments[3]) != self.source:
                raise AssertionError(
                    f"unexpected subvolume path: {arguments[3]}"
                )

            if self.fail_subvolume:
                raise subprocess.CalledProcessError(
                    1,
                    arguments,
                    stderr="not a subvolume",
                )

            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout="",
                stderr="",
            )

        if arguments[:4] == [
            "btrfs",
            "filesystem",
            "show",
            "--raw",
        ]:
            target = Path(arguments[4])

            if target == self.source:
                filesystem_uuid = self.source_uuid
            elif target == self.snapshot_mount:
                filesystem_uuid = self.snapshot_uuid
            else:
                raise AssertionError(
                    f"unexpected filesystem path: {target}"
                )

            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout=(
                    "Label: none  uuid: "
                    f"{filesystem_uuid}\n"
                ),
                stderr="",
            )

        raise AssertionError(
            f"unexpected preflight command: {arguments}"
        )


class LockTests(unittest.TestCase):
    def test_overlapping_backup_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            lock = Path(temporary) / "minecraft-backup.lock"

            with backup.exclusive_backup_lock(lock):
                with self.assertRaisesRegex(
                    backup.BackupError,
                    "another Minecraft backup is already running",
                ):
                    with backup.exclusive_backup_lock(lock):
                        self.fail(
                            "overlapping backup unexpectedly acquired lock"
                        )

    def test_backup_lock_is_reusable_after_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            lock = Path(temporary) / "minecraft-backup.lock"

            with backup.exclusive_backup_lock(lock):
                pass

            with backup.exclusive_backup_lock(lock):
                pass


class PreflightTests(unittest.TestCase):
    @staticmethod
    def mounted(source, snapshot_mount):
        mounted_paths = {
            source,
            snapshot_mount,
        }
        return lambda path: Path(path) in mounted_paths

    def test_preflight_prepares_secure_snapshot_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"
            snapshot_root = snapshot_mount / "minecraft"

            source.mkdir()
            snapshot_mount.mkdir()

            runner = FakePreflightRunner(
                source,
                snapshot_mount,
            )

            plan = backup.prepare_snapshot(
                source=source,
                snapshot_mount=snapshot_mount,
                snapshot_root=snapshot_root,
                now=datetime(
                    2026,
                    10,
                    10,
                    18,
                    0,
                    0,
                    tzinfo=timezone.utc,
                ),
                runner=runner,
                mount_checker=self.mounted(
                    source,
                    snapshot_mount,
                ),
            )

            self.assertEqual(
                plan.source,
                source,
            )
            self.assertEqual(
                plan.destination,
                (
                    snapshot_root
                    / "survival-20261010T180000Z"
                ),
            )
            self.assertEqual(
                snapshot_root.stat().st_mode & 0o777,
                0o700,
            )
            self.assertEqual(
                runner.calls,
                [
                    [
                        "btrfs",
                        "subvolume",
                        "show",
                        str(source),
                    ],
                    ["btrfs", "subvolume", "list", "-o", str(source)],
                    [
                        "btrfs",
                        "filesystem",
                        "show",
                        "--raw",
                        str(source),
                    ],
                    [
                        "btrfs",
                        "filesystem",
                        "show",
                        "--raw",
                        str(snapshot_mount),
                    ],
                ],
            )

    def test_preflight_rejects_source_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_source = root / "real-source"
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"

            real_source.mkdir()
            source.symlink_to(
                real_source,
                target_is_directory=True,
            )
            snapshot_mount.mkdir()

            runner = FakePreflightRunner(
                source,
                snapshot_mount,
            )

            with self.assertRaisesRegex(
                backup.BackupError,
                "must not be a symbolic link",
            ):
                backup.prepare_snapshot(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=(
                        snapshot_mount / "minecraft"
                    ),
                    runner=runner,
                    mount_checker=self.mounted(
                        source,
                        snapshot_mount,
                    ),
                )

            self.assertEqual(runner.calls, [])

    def test_preflight_requires_expected_mount_points(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"

            source.mkdir()
            snapshot_mount.mkdir()

            runner = FakePreflightRunner(
                source,
                snapshot_mount,
            )

            with self.assertRaisesRegex(
                backup.BackupError,
                "Minecraft source must be a mount point",
            ):
                backup.prepare_snapshot(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=(
                        snapshot_mount / "minecraft"
                    ),
                    runner=runner,
                    mount_checker=lambda _path: False,
                )

            self.assertEqual(runner.calls, [])

    def test_preflight_rejects_non_subvolume_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"

            source.mkdir()
            snapshot_mount.mkdir()

            runner = FakePreflightRunner(
                source,
                snapshot_mount,
                fail_subvolume=True,
            )

            with self.assertRaisesRegex(
                backup.BackupError,
                "Btrfs preflight command failed",
            ):
                backup.prepare_snapshot(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=(
                        snapshot_mount / "minecraft"
                    ),
                    runner=runner,
                    mount_checker=self.mounted(
                        source,
                        snapshot_mount,
                    ),
                )

    def test_preflight_rejects_different_btrfs_filesystems(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"

            source.mkdir()
            snapshot_mount.mkdir()

            runner = FakePreflightRunner(
                source,
                snapshot_mount,
                snapshot_uuid=FakePreflightRunner.OTHER_UUID,
            )

            with self.assertRaisesRegex(
                backup.BackupError,
                "different Btrfs filesystems",
            ):
                backup.prepare_snapshot(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=(
                        snapshot_mount / "minecraft"
                    ),
                    runner=runner,
                    mount_checker=self.mounted(
                        source,
                        snapshot_mount,
                    ),
                )

    def test_preflight_rejects_snapshot_root_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"
            snapshot_root = snapshot_mount / "minecraft"
            target = root / "elsewhere"

            source.mkdir()
            snapshot_mount.mkdir()
            target.mkdir()
            snapshot_root.symlink_to(
                target,
                target_is_directory=True,
            )

            runner = FakePreflightRunner(
                source,
                snapshot_mount,
            )

            with self.assertRaisesRegex(
                backup.BackupError,
                "snapshot root must not be a symbolic link",
            ):
                backup.prepare_snapshot(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=snapshot_root,
                    runner=runner,
                    mount_checker=self.mounted(
                        source,
                        snapshot_mount,
                    ),
                )

    def test_preflight_rejects_snapshot_root_mount_point(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"
            snapshot_root = snapshot_mount / "minecraft"

            source.mkdir()
            snapshot_mount.mkdir()
            snapshot_root.mkdir()

            runner = FakePreflightRunner(
                source,
                snapshot_mount,
            )

            mounted_paths = {
                source,
                snapshot_mount,
                snapshot_root,
            }

            with self.assertRaisesRegex(
                backup.BackupError,
                "snapshot root must not be a mount point",
            ):
                backup.prepare_snapshot(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=snapshot_root,
                    runner=runner,
                    mount_checker=lambda path: (
                        Path(path) in mounted_paths
                    ),
                )

    def test_preflight_rejects_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"
            snapshot_root = snapshot_mount / "minecraft"

            source.mkdir()
            snapshot_mount.mkdir()
            snapshot_root.mkdir()

            now = datetime(
                2026,
                10,
                10,
                18,
                0,
                0,
                tzinfo=timezone.utc,
            )

            destination = backup.snapshot_destination(
                snapshot_root=snapshot_root,
                now=now,
            )
            destination.mkdir()

            runner = FakePreflightRunner(
                source,
                snapshot_mount,
            )

            with self.assertRaisesRegex(
                backup.BackupError,
                "snapshot destination already exists",
            ):
                backup.prepare_snapshot(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=snapshot_root,
                    now=now,
                    runner=runner,
                    mount_checker=self.mounted(
                        source,
                        snapshot_mount,
                    ),
                )

    def test_abandoned_recovery_precedes_preflight_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_source = root / "real-source"
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"
            marker = (
                root
                / "runtime"
                / "autosave-needs-restore"
            )

            real_source.mkdir()
            source.symlink_to(
                real_source,
                target_is_directory=True,
            )
            snapshot_mount.mkdir()

            backup.create_autosave_recovery_marker(
                marker=marker,
            )

            recovery_socket = FakeWebSocket(
                [
                    response(1, True),
                ]
            )
            factory = ConnectionFactory(
                recovery_socket,
            )

            with self.assertRaisesRegex(
                backup.BackupError,
                "must not be a symbolic link",
            ):
                backup.perform_snapshot_backup(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=(
                        snapshot_mount / "minecraft"
                    ),
                    preflight_runner=FakePreflightRunner(
                        source,
                        snapshot_mount,
                    ),
                    snapshot_runner=lambda *_args, **_kwargs: (
                        self.fail(
                            "snapshot command ran after failed preflight"
                        )
                    ),
                    mount_checker=self.mounted(
                        source,
                        snapshot_mount,
                    ),
                    connection_factory=factory,
                    rpc_timeout=1,
                    recovery_marker=marker,
                )

            self.assertEqual(factory.calls, 1)
            self.assertFalse(marker.exists())
            self.assertEqual(
                recovery_socket.sent[0]["method"],
                backup.msmp.AUTOSAVE_SET_METHOD,
            )
            self.assertEqual(
                recovery_socket.sent[0]["params"],
                {"enable": True},
            )

    def test_preflight_failure_happens_before_management_connection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_source = root / "real-source"
            source = root / "source"
            snapshot_mount = root / "snapshot-mount"
            marker = (
                root
                / "runtime"
                / "autosave-needs-restore"
            )

            real_source.mkdir()
            source.symlink_to(
                real_source,
                target_is_directory=True,
            )
            snapshot_mount.mkdir()

            factory = ConnectionFactory()

            with self.assertRaises(backup.BackupError):
                backup.perform_snapshot_backup(
                    source=source,
                    snapshot_mount=snapshot_mount,
                    snapshot_root=(
                        snapshot_mount / "minecraft"
                    ),
                    preflight_runner=FakePreflightRunner(
                        source,
                        snapshot_mount,
                    ),
                    snapshot_runner=lambda *_args, **_kwargs: (
                        self.fail(
                            "snapshot command ran after failed preflight"
                        )
                    ),
                    mount_checker=self.mounted(
                        source,
                        snapshot_mount,
                    ),
                    connection_factory=factory,
                    recovery_marker=marker,
                )

            self.assertEqual(factory.calls, 0)
            self.assertFalse(marker.exists())


class SnapshotTests(unittest.TestCase):
    def test_snapshot_command_is_minimal_read_only_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            destination = root / "survival-test"

            calls = []

            def runner(arguments, check, timeout, capture_output, text):
                self.assertTrue(check)
                self.assertEqual(
                    timeout,
                    backup.DEFAULT_SNAPSHOT_TIMEOUT,
                )
                calls.append(arguments)

            plan = backup.SnapshotPlan(
                source=source,
                destination=destination,
            )

            result = backup.create_readonly_snapshot(
                plan,
                runner=runner,
            )

            self.assertEqual(result, destination)
            self.assertEqual(
                calls,
                [
                    [
                        "btrfs",
                        "subvolume",
                        "snapshot",
                        "-r",
                        str(source),
                        str(destination),
                    ]
                ],
            )

    def test_btrfs_failure_is_propagated(self):
        plan = backup.SnapshotPlan(
            source=Path("/source"),
            destination=Path("/snapshot"),
        )

        def runner(_arguments, check, timeout, capture_output, text):
            self.assertTrue(check)
            self.assertEqual(
                timeout,
                backup.DEFAULT_SNAPSHOT_TIMEOUT,
            )
            raise subprocess.CalledProcessError(
                1,
                ["btrfs"],
            )

        with self.assertRaises(
            subprocess.CalledProcessError
        ):
            backup.create_readonly_snapshot(
                plan,
                runner=runner,
            )

    def test_snapshot_timeout_is_propagated(self):
        plan = backup.SnapshotPlan(
            source=Path("/source"),
            destination=Path("/snapshot"),
        )

        def runner(arguments, check, timeout, capture_output, text):
            self.assertTrue(check)
            raise subprocess.TimeoutExpired(
                arguments,
                timeout,
            )

        with self.assertRaises(
            subprocess.TimeoutExpired
        ) as context:
            backup.create_readonly_snapshot(
                plan,
                runner=runner,
            )

        self.assertEqual(
            context.exception.timeout,
            backup.DEFAULT_SNAPSHOT_TIMEOUT,
        )


class MarkerTests(unittest.TestCase):
    def test_marker_lifecycle(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            self.assertFalse(
                backup.autosave_recovery_needed(marker)
            )

            backup.create_autosave_recovery_marker(
                marker=marker,
            )

            self.assertTrue(
                backup.autosave_recovery_needed(marker)
            )
            self.assertEqual(
                marker.stat().st_mode & 0o777,
                0o600,
            )
            self.assertEqual(
                marker.parent.stat().st_mode & 0o777,
                0o700,
            )

            backup.clear_autosave_recovery_marker(
                marker=marker,
            )

            self.assertFalse(
                backup.autosave_recovery_needed(marker)
            )

    def test_recovery_without_marker_is_noop(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )
            factory = ConnectionFactory()

            recovered = backup.recover_abandoned_autosave(
                marker=marker,
                connection_factory=factory,
                rpc_timeout=1,
            )

            self.assertFalse(recovered)
            self.assertEqual(factory.calls, 0)

    def test_abandoned_marker_is_recovered_and_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            backup.create_autosave_recovery_marker(
                marker=marker,
            )

            recovery_socket = FakeWebSocket(
                [
                    response(1, True),
                ]
            )
            factory = ConnectionFactory(
                recovery_socket,
            )

            recovered = backup.recover_abandoned_autosave(
                marker=marker,
                connection_factory=factory,
                rpc_timeout=1,
            )

            self.assertTrue(recovered)
            self.assertFalse(marker.exists())
            self.assertEqual(factory.calls, 1)
            self.assertEqual(
                recovery_socket.sent[0]["method"],
                backup.msmp.AUTOSAVE_SET_METHOD,
            )
            self.assertEqual(
                recovery_socket.sent[0]["params"],
                {"enable": True},
            )

    def test_failed_abandoned_recovery_keeps_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            backup.create_autosave_recovery_marker(
                marker=marker,
            )

            recovery_socket = FakeWebSocket(
                [
                    response(1, False),
                ]
            )

            with self.assertRaises(
                backup.msmp.ProtocolError
            ):
                backup.recover_abandoned_autosave(
                    marker=marker,
                    connection_factory=ConnectionFactory(
                        recovery_socket,
                    ),
                    rpc_timeout=1,
                )

            self.assertTrue(marker.exists())


class RecoveryTests(unittest.TestCase):
    def test_normal_transaction_uses_one_connection(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            websocket = FakeWebSocket(
                [
                    response(1, discovery()),
                    response(2, True),
                    response(3, False),
                    response(4, False),
                    response(5, True),
                    notification(
                        backup.msmp.SAVING_NOTIFICATION
                    ),
                    notification(
                        backup.msmp.SAVED_NOTIFICATION
                    ),
                    response(6, True),
                ]
            )

            factory = ConnectionFactory(websocket)
            actions = []

            def snapshot_action():
                self.assertTrue(marker.exists())
                actions.append("snapshot")
                return "done"

            result = backup.perform_backup(
                action=snapshot_action,
                connection_factory=factory,
                rpc_timeout=1,
                save_timeout=1,
                recovery_marker=marker,
            )

            self.assertEqual(result, "done")
            self.assertEqual(actions, ["snapshot"])
            self.assertEqual(factory.calls, 1)
            self.assertFalse(marker.exists())

    def test_failed_normal_restore_uses_fresh_connection(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            transaction_socket = FakeWebSocket(
                [
                    response(1, discovery()),
                    response(2, True),
                    response(3, False),
                    response(4, False),
                    response(5, True),
                    notification(
                        backup.msmp.SAVING_NOTIFICATION
                    ),
                    notification(
                        backup.msmp.SAVED_NOTIFICATION
                    ),
                    response(6, False),
                ]
            )

            recovery_socket = FakeWebSocket(
                [
                    response(1, True),
                ]
            )

            factory = ConnectionFactory(
                transaction_socket,
                recovery_socket,
            )

            with self.assertRaises(backup.BackupError):
                backup.perform_backup(
                    action=lambda: "snapshot-created",
                    connection_factory=factory,
                    rpc_timeout=1,
                    save_timeout=1,
                    recovery_marker=marker,
                )

            self.assertEqual(factory.calls, 2)
            self.assertFalse(marker.exists())
            self.assertEqual(
                recovery_socket.sent[0]["method"],
                backup.msmp.AUTOSAVE_SET_METHOD,
            )
            self.assertEqual(
                recovery_socket.sent[0]["params"],
                {"enable": True},
            )

    def test_failed_recovery_preserves_both_failures_and_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            transaction_socket = FakeWebSocket(
                [
                    response(1, discovery()),
                    response(2, True),
                    response(3, False),
                    response(4, False),
                    response(5, True),
                    notification(
                        backup.msmp.SAVING_NOTIFICATION
                    ),
                    notification(
                        backup.msmp.SAVED_NOTIFICATION
                    ),
                    response(6, False),
                ]
            )

            recovery_socket = FakeWebSocket(
                [
                    response(1, False),
                ]
            )

            factory = ConnectionFactory(
                transaction_socket,
                recovery_socket,
            )

            with self.assertRaises(
                backup.BackupRecoveryError
            ):
                backup.perform_backup(
                    action=lambda: "snapshot-created",
                    connection_factory=factory,
                    rpc_timeout=1,
                    save_timeout=1,
                    recovery_marker=marker,
                )

            self.assertEqual(factory.calls, 2)
            self.assertTrue(marker.exists())

    def test_action_and_same_session_restore_failure_can_recover_fresh(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            transaction_socket = FakeWebSocket(
                [
                    response(1, discovery()),
                    response(2, True),
                    response(3, False),
                    response(4, False),
                    response(5, True),
                    notification(
                        backup.msmp.SAVING_NOTIFICATION
                    ),
                    notification(
                        backup.msmp.SAVED_NOTIFICATION
                    ),
                    response(6, False),
                ]
            )

            recovery_socket = FakeWebSocket(
                [
                    response(1, True),
                ]
            )

            factory = ConnectionFactory(
                transaction_socket,
                recovery_socket,
            )

            def fail_snapshot():
                self.assertTrue(marker.exists())
                raise RuntimeError("snapshot failed")

            with self.assertRaisesRegex(
                RuntimeError,
                "snapshot failed",
            ):
                backup.perform_backup(
                    action=fail_snapshot,
                    connection_factory=factory,
                    rpc_timeout=1,
                    save_timeout=1,
                    recovery_marker=marker,
                )

            self.assertEqual(factory.calls, 2)
            self.assertFalse(marker.exists())


    def test_snapshot_timeout_restores_autosave_and_clears_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            transaction_socket = FakeWebSocket(
                [
                    response(1, discovery()),
                    response(2, True),
                    response(3, False),
                    response(4, False),
                    response(5, True),
                    notification(
                        backup.msmp.SAVING_NOTIFICATION
                    ),
                    notification(
                        backup.msmp.SAVED_NOTIFICATION
                    ),
                    response(6, True),
                ]
            )

            factory = ConnectionFactory(
                transaction_socket,
            )

            def timeout_snapshot():
                self.assertTrue(marker.exists())
                raise subprocess.TimeoutExpired(
                    ["btrfs"],
                    backup.DEFAULT_SNAPSHOT_TIMEOUT,
                )

            with self.assertRaises(
                subprocess.TimeoutExpired
            ):
                backup.perform_backup(
                    action=timeout_snapshot,
                    connection_factory=factory,
                    rpc_timeout=1,
                    save_timeout=1,
                    recovery_marker=marker,
                )

            self.assertEqual(factory.calls, 1)
            self.assertFalse(marker.exists())
            self.assertEqual(
                transaction_socket.sent[-1]["method"],
                backup.msmp.AUTOSAVE_SET_METHOD,
            )
            self.assertEqual(
                transaction_socket.sent[-1]["params"],
                {"enable": True},
            )

    def test_snapshot_timeout_and_failed_recovery_keeps_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = (
                Path(temporary)
                / "runtime"
                / "autosave-needs-restore"
            )

            transaction_socket = FakeWebSocket(
                [
                    response(1, discovery()),
                    response(2, True),
                    response(3, False),
                    response(4, False),
                    response(5, True),
                    notification(
                        backup.msmp.SAVING_NOTIFICATION
                    ),
                    notification(
                        backup.msmp.SAVED_NOTIFICATION
                    ),
                    response(6, False),
                ]
            )

            recovery_socket = FakeWebSocket(
                [
                    response(1, False),
                ]
            )

            factory = ConnectionFactory(
                transaction_socket,
                recovery_socket,
            )

            def timeout_snapshot():
                raise subprocess.TimeoutExpired(
                    ["btrfs"],
                    backup.DEFAULT_SNAPSHOT_TIMEOUT,
                )

            with self.assertRaises(
                backup.BackupRecoveryError
            ) as context:
                backup.perform_backup(
                    action=timeout_snapshot,
                    connection_factory=factory,
                    rpc_timeout=1,
                    save_timeout=1,
                    recovery_marker=marker,
                )

            self.assertIsInstance(
                context.exception.transaction_error.primary_error,
                subprocess.TimeoutExpired,
            )
            self.assertEqual(factory.calls, 2)
            self.assertTrue(marker.exists())


class PersistentMetadataTests(unittest.TestCase):
    FS = "11111111-1111-1111-1111-111111111111"
    ID = "22222222-2222-2222-2222-222222222222"
    TIME = "2026-10-10T18:00:00Z"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / "state"
        self.snapshots = self.root / "snapshots"
        self.snapshots.mkdir(mode=0o700)
        self.state, self.manifest = backup.load_metadata(self.directory, self.snapshots, create=True)
        self.path = self.snapshots / "survival-20261010T180000Z"

    def pending(self):
        self.state["pending_snapshot"] = {"path": str(self.path), "planned_at": self.TIME,
                                          "source_filesystem_uuid": self.FS}
        backup.atomic_json(self.directory / "state.json", self.state)

    def runner(self, arguments, **kwargs):
        self.assertTrue(kwargs["check"])
        if arguments[1:3] == ["subvolume", "show"]:
            output = "UUID: " + self.ID + "\nParent UUID: " + self.FS + "\n"
        elif arguments[1:3] == ["filesystem", "show"]:
            output = "Label: none uuid: " + self.FS + "\n"
        elif arguments[1:3] in (["subvolume", "list"], ["filesystem", "sync"]):
            output = ""
        elif arguments[1:3] == ["property", "get"]:
            output = "ro=true\n"
        else:
            self.fail("unexpected command: " + repr(arguments))
        return subprocess.CompletedProcess(arguments, 0, stdout=output)

    def reconcile(self, runner=None, mount_checker=lambda path: False):
        backup.register_pending(self.state, self.manifest, self.directory, self.snapshots,
                                runner or self.runner, mount_checker)

    def test_missing_files_and_read_only_initial_state(self):
        absent = self.root / "absent"
        state, manifest = backup.load_metadata(absent, self.snapshots)
        self.assertFalse(absent.exists())
        self.assertIsNone(state["pending_snapshot"])
        self.assertEqual(manifest["snapshots"], [])
        self.assertEqual(self.directory.stat().st_mode & 0o777, 0o700)

    def test_state_directory_refuses_symlink_file_and_bad_mode(self):
        for kind in ("symlink", "file", "mode"):
            with self.subTest(kind=kind):
                target = self.root / kind
                if kind == "symlink":
                    target.symlink_to(self.directory)
                elif kind == "file":
                    target.touch()
                else:
                    target.mkdir(mode=0o755)
                with self.assertRaises(backup.BackupError):
                    backup.load_metadata(target, self.snapshots, create=True)

    def test_schema_and_field_rejection_matrix(self):
        import copy
        mutations = [
            lambda s, m: s.pop("schema_version"),
            lambda s, m: s.update(schema_version="1"),
            lambda s, m: s.update(schema_version=True),
            lambda s, m: s.update(schema_version=1),
            lambda s, m: s.update(pending_snapshot=[]),
            lambda s, m: s.update(last_attempt={}),
            lambda s, m: s.update(last_success={}),
            lambda s, m: s.update(last_retention={}),
            lambda s, m: m.update(snapshots={}),
        ]
        for mutate in mutations:
            state, manifest = copy.deepcopy(self.state), copy.deepcopy(self.manifest)
            mutate(state, manifest)
            with self.subTest(state=state, manifest=manifest), self.assertRaises(backup.BackupError):
                backup.validate_metadata(state, manifest, self.snapshots)
        with self.assertRaises(backup.BackupError):
            backup.validate_metadata([], self.manifest, self.snapshots)

    def test_json_malformed_duplicate_and_unsafe_files(self):
        path = self.directory / "state.json"
        for content in ('{', '{"schema_version":1,"schema_version":1}', '[]'):
            path.write_text(content)
            path.chmod(0o600)
            with self.subTest(content=content), self.assertRaises(backup.BackupError):
                backup.load_metadata(self.directory, self.snapshots)
        path.unlink()
        path.symlink_to(self.root / "absent")
        with self.assertRaises(backup.BackupError):
            backup.load_metadata(self.directory, self.snapshots)
        path.unlink()
        path.write_text('{}')
        path.chmod(0o644)
        with self.assertRaises(backup.BackupError):
            backup.load_metadata(self.directory, self.snapshots)

    def record(self):
        return {"name": self.path.name, "path": str(self.path), "created_at": self.TIME,
                "filesystem_uuid": self.FS, "subvolume_uuid": self.ID}

    def test_manifest_path_uuid_time_and_duplicate_matrix(self):
        import copy
        invalid = [
            {"path": str(self.root / self.path.name)},
            {"path": str(self.snapshots / "nested" / self.path.name)},
            {"name": "../escape"}, {"created_at": "2026-10-10T18:00:00+00:00"},
            {"created_at": "2026-02-30T18:00:00Z"}, {"filesystem_uuid": "invalid"},
            {"subvolume_uuid": None},
        ]
        for changes in invalid:
            record = self.record()
            record.update(changes)
            with self.subTest(changes=changes), self.assertRaises(backup.BackupError):
                backup.validate_metadata(self.state, {"schema_version": 2, "snapshots": [record]}, self.snapshots)
        for duplicate in (self.record(), dict(self.record(), name="survival-20261010T190000Z",
                                             path=str(self.snapshots / "survival-20261010T190000Z"))):
            with self.assertRaises(backup.BackupError):
                backup.validate_metadata(self.state, {"schema_version": 2, "snapshots": [self.record(), copy.deepcopy(duplicate)]}, self.snapshots)

    def test_atomic_write_and_stale_temp(self):
        stale = self.directory / ".minecraft-stale"
        stale.write_text("partial")
        path = self.directory / "state.json"
        backup.atomic_json(path, self.state)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(path.read_text()), self.state)
        self.assertEqual(stale.read_text(), "partial")

    def test_atomic_failures_preserve_complete_final(self):
        from unittest.mock import patch
        path = self.directory / "state.json"
        backup.atomic_json(path, self.state)
        before = path.read_bytes()
        changed = dict(self.state, last_attempt={"started_at": self.TIME,
                                                "finished_at": self.TIME, "result": "success"})
        for operation in ("json.dump", "os.fsync", "os.replace"):
            with self.subTest(operation=operation):
                with patch.object(backup.json if operation.startswith("json") else backup.os,
                                  operation.split(".")[1], side_effect=OSError("injected")):
                    with self.assertRaises(OSError):
                        backup.atomic_json(path, changed)
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(list(self.directory.glob(".minecraft-*")), [])
        original = backup.os.fsync
        def fail_directory(descriptor):
            import stat
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError("directory fsync failed")
            original(descriptor)
        with patch.object(backup.os, "fsync", side_effect=fail_directory):
            with self.assertRaises(OSError):
                backup.atomic_json(path, changed)
        self.assertEqual(json.loads(path.read_text()), changed)

    def test_pending_absent_is_aborted(self):
        self.pending()
        self.reconcile()
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNone(state["pending_snapshot"])
        self.assertEqual(state["last_attempt"]["result"], "aborted")
        self.assertEqual(manifest["snapshots"], [])

    def test_pending_adoption_and_already_registered_are_idempotent(self):
        self.pending()
        self.path.mkdir()
        self.reconcile()
        self.assertEqual(self.manifest["snapshots"], [self.record()])
        self.pending()
        self.reconcile()
        self.assertEqual(len(self.manifest["snapshots"]), 1)
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNone(state["pending_snapshot"])
        self.assertEqual(state["last_success"]["snapshot_uuid"], self.ID)

    def test_pending_identity_mismatch_matrix(self):
        self.pending()
        self.path.mkdir()
        for command, replacement in (("filesystem", "Label: none uuid: " + self.ID),
                                     ("property", "ro=false"), ("subvolume", "UUID: garbage")):
            def runner(arguments, **kwargs):
                result = self.runner(arguments, **kwargs)
                if arguments[1] == command:
                    result.stdout = replacement
                return result
            with self.subTest(command=command), self.assertRaises(backup.BackupError):
                self.reconcile(runner=runner)
            self.assertIsNotNone(backup.load_metadata(self.directory, self.snapshots)[0]["pending_snapshot"])
        self.manifest["snapshots"] = [dict(self.record(), subvolume_uuid=self.FS)]
        with self.assertRaises(backup.BackupError):
            self.reconcile()

    def test_pending_symlink_and_mountpoint_refused(self):
        self.pending()
        self.path.symlink_to(self.directory)
        with self.assertRaises(backup.BackupError):
            self.reconcile()
        self.path.unlink()
        self.path.mkdir()
        with self.assertRaises(backup.BackupError):
            self.reconcile(mount_checker=lambda path: path == self.path)

    def test_registration_state_failure_is_reconcilable(self):
        from unittest.mock import patch
        self.pending()
        self.path.mkdir()
        writer = backup.atomic_json
        def fail_state(path, value):
            if path.name == "state.json":
                raise OSError("injected state failure")
            writer(path, value)
        with patch.object(backup, "atomic_json", side_effect=fail_state):
            with self.assertRaises(OSError):
                self.reconcile()
        self.state, self.manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNotNone(self.state["pending_snapshot"])
        self.assertEqual(len(self.manifest["snapshots"]), 1)
        self.reconcile()
        self.assertIsNone(backup.load_metadata(self.directory, self.snapshots)[0]["pending_snapshot"])

    def test_manifest_failure_keeps_pending_and_reconciles(self):
        from unittest.mock import patch
        self.pending()
        self.path.mkdir()
        with patch.object(backup.os, "replace", side_effect=OSError("injected")):
            with self.assertRaises(OSError):
                self.reconcile()
        self.state, self.manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNotNone(self.state["pending_snapshot"])
        self.assertEqual(self.manifest["snapshots"], [])
        self.reconcile()

    def test_filesystem_identity_fallback_handles_nested_and_readonly_paths(self):
        from unittest.mock import patch
        def unavailable(arguments, **kwargs):
            raise subprocess.CalledProcessError(1, arguments)
        def fs_info(fd, request, info, mutate):
            self.assertEqual(request, 0x8400941F)
            self.assertEqual(len(info), 1024)
            info[16:32] = backup.UUID(self.FS).bytes
        with patch.object(backup.fcntl, "ioctl", side_effect=fs_info):
            self.assertEqual(backup.btrfs_filesystem_uuid(self.root, runner=unavailable), self.FS)
        with patch.object(backup.fcntl, "ioctl", side_effect=OSError("not Btrfs")):
            with self.assertRaises(backup.BackupError):
                backup.btrfs_filesystem_uuid(self.root, runner=unavailable)
        with patch.object(backup.fcntl, "ioctl", side_effect=lambda fd, request, info, mutate: None):
            with self.assertRaises(backup.BackupError):
                backup.btrfs_filesystem_uuid(self.root, runner=unavailable)

    def test_kernel_mount_table_distinguishes_subvolumes_and_bind_mounts(self):
        table = self.root / "mountinfo"
        table.write_text("40 1 0:30 /@snapshots /snapshots rw - btrfs /dev/fake rw\n"
                         "41 40 0:30 /@snapshots/manual /snapshots/bind\\040mount rw - btrfs /dev/fake rw\n")
        self.assertTrue(backup.is_mountpoint(Path('/snapshots'), table))
        self.assertTrue(backup.is_mountpoint(Path('/snapshots/bind mount'), table))
        self.assertFalse(backup.is_mountpoint(Path('/snapshots/unmounted-subvolume'), table))

    def managed_arguments(self, runner):
        source = self.root / "source"
        source.mkdir(exist_ok=True)
        return dict(directory=self.directory, source=source, snapshot_mount=self.root,
                    snapshot_root=self.snapshots, runner=runner,
                    mount_checker=lambda path: path in (source, self.root),
                    recovery_marker=self.root / "runtime" / "marker",
                    now=datetime(2026, 10, 10, 18, tzinfo=timezone.utc))

    def test_managed_transaction_pending_precedes_snapshot_and_registration_follows_restore(self):
        from unittest.mock import patch
        def runner(arguments, **kwargs):
            if arguments[1:3] == ["subvolume", "snapshot"]:
                durable, manifest = backup.load_metadata(self.directory, self.snapshots)
                self.assertEqual(durable["pending_snapshot"]["path"], str(self.path))
                self.assertEqual(manifest["snapshots"], [])
                self.path.mkdir()
                return subprocess.CompletedProcess(arguments, 0)
            return self.runner(arguments, **kwargs)
        restored = False
        def transaction(action, **kwargs):
            nonlocal restored
            result = action()
            self.assertIsNotNone(backup.load_metadata(self.directory, self.snapshots)[0]["pending_snapshot"])
            restored = True
            return result
        original = backup.verify_snapshot_identity
        def verify(*args, **kwargs):
            self.assertTrue(restored)
            return original(*args, **kwargs)
        with patch.object(backup, "wait_for_management"), patch.object(backup, "perform_backup", side_effect=transaction), patch.object(backup, "verify_snapshot_identity", side_effect=verify):
            backup.perform_managed_backup(**self.managed_arguments(runner))
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertEqual(state["last_attempt"]["result"], "success")
        self.assertEqual(len(manifest["snapshots"]), 1)
        self.assertIsNone(state["pending_snapshot"])

    def test_nested_bind_and_foreign_mounts_refuse_before_readiness(self):
        from unittest.mock import patch
        source = self.root / "source"
        for kind, filesystem in (("bind", "btrfs"), ("foreign", "ext4")):
            with self.subTest(kind=kind):
                mountinfo = self.root / "mountinfo"
                mountinfo.write_text(f"1 0 0:1 / {source} rw - btrfs /dev/test rw\n"
                                     f"2 1 0:2 / {source}/survival/database rw - {filesystem} /dev/other rw\n")
                parser = backup.mounted_paths
                with patch.object(backup, "mounted_paths", side_effect=lambda: parser(mountinfo)), patch.object(backup, "wait_for_management") as readiness, self.assertRaises(backup.BackupError):
                    backup.perform_managed_backup(**self.managed_arguments(self.runner))
                readiness.assert_not_called()
                state, manifest = backup.load_metadata(self.directory, self.snapshots)
                self.assertIsNone(state["pending_snapshot"])
                self.assertEqual(manifest["snapshots"], [])
                self.assertEqual(state["last_attempt"]["stage"], "preflight")

    def test_mount_ancestry_ignores_source_itself_and_similarly_named_sibling(self):
        from unittest.mock import patch
        source = self.root / "source"
        mounts = {source, self.root / "source-other" / "database", Path("/")}
        with patch.object(backup, "mounted_paths", return_value=mounts):
            backup.prepare_snapshot(source=source, **{
                key: value for key, value in self.managed_arguments(self.runner).items()
                if key in ("snapshot_mount", "snapshot_root", "runner", "mount_checker", "now")
            })

    def test_live_status_verifies_recovery_point_without_writes_or_management(self):
        from unittest.mock import patch
        self.pending()
        self.path.mkdir()
        self.reconcile()
        arguments = self.managed_arguments(self.runner)
        before = {path: path.read_bytes() for path in self.directory.iterdir()}
        with patch.object(backup.msmp, "open_connection", side_effect=AssertionError("must not connect")):
            report = backup.live_status_report(self.state, self.manifest, **{
                key: value for key, value in arguments.items()
                if key in ("source", "snapshot_mount", "snapshot_root", "runner", "mount_checker")
            })
        self.assertEqual(report["live_verification"], "passed")
        self.assertEqual(before, {path: path.read_bytes() for path in self.directory.iterdir()})

    def test_live_status_audits_old_records_and_source_completeness(self):
        from unittest.mock import patch
        self.pending()
        self.path.mkdir()
        self.reconcile()
        old = dict(self.record(), name="survival-20261010T120000Z",
                   path=str(self.snapshots / "survival-20261010T120000Z"),
                   created_at="2026-10-10T12:00:00Z",
                   subvolume_uuid="11111111-1111-4111-8111-111111111111")
        oldpath = Path(old["path"])
        oldpath.mkdir()
        self.manifest["snapshots"].insert(0, old)
        unknown = self.snapshots / "unmanaged"
        unknown.mkdir()
        arguments = self.managed_arguments(self.runner)
        for kind in ("valid", "nested", "missing", "replaced", "readwrite", "mounted"):
            with self.subTest(kind=kind):
                if kind == "missing":
                    oldpath.rmdir()
                def runner(command, **kwargs):
                    self.assertNotIn(str(unknown), command)
                    result = self.runner(command, **kwargs)
                    if command[1:3] == ["subvolume", "list"] and kind == "nested":
                        result.stdout = "ID 123 path nested\n"
                    if str(oldpath) in command:
                        if command[1:3] == ["subvolume", "show"]:
                            result.stdout = "UUID: " + (self.ID if kind == "replaced" else old["subvolume_uuid"])
                        if command[1:3] == ["property", "get"] and kind == "readwrite":
                            result.stdout = "ro=false"
                    return result
                check = lambda path: arguments["mount_checker"](path) or (kind == "mounted" and path == oldpath)
                before = {path: path.read_bytes() for path in self.directory.iterdir()}
                with patch.object(backup.msmp, "open_connection", side_effect=AssertionError("must not connect")):
                    report = backup.live_status_report(self.state, self.manifest,
                        source=arguments["source"], snapshot_mount=self.root, snapshot_root=self.snapshots,
                        runner=runner, mount_checker=check)
                self.assertEqual(report["live_verification"], "passed" if kind == "valid" else "failed")
                self.assertEqual(before, {path: path.read_bytes() for path in self.directory.iterdir()})
                if kind == "missing":
                    oldpath.mkdir()

    def test_live_status_checks_all_fourteen_owned_recovery_points(self):
        from unittest.mock import patch
        self.pending()
        self.path.mkdir()
        self.reconcile()
        for hour in range(13):
            record = dict(self.record(), name=f"survival-20261010T{hour:02d}0000Z",
                          path=str(self.snapshots / f"survival-20261010T{hour:02d}0000Z"),
                          created_at=f"2026-10-10T{hour:02d}:00:00Z",
                          subvolume_uuid=f"00000000-0000-4000-8000-{hour:012d}")
            Path(record["path"]).mkdir()
            self.manifest["snapshots"].append(record)
        visited = set()
        original = backup.verify_snapshot_identity
        identities = {record["path"]: record["subvolume_uuid"] for record in self.manifest["snapshots"]}
        def runner(command, **kwargs):
            result = self.runner(command, **kwargs)
            if command[1:3] == ["subvolume", "show"] and command[-1] in identities:
                result.stdout = "UUID: " + identities[command[-1]]
            return result
        def verify(path, *args, **kwargs):
            visited.add(str(path))
            return original(path, *args, **kwargs)
        arguments = self.managed_arguments(runner)
        with patch.object(backup, "verify_snapshot_identity", side_effect=verify):
            report = backup.live_status_report(self.state, self.manifest, **{
                key: value for key, value in arguments.items()
                if key in ("source", "snapshot_mount", "snapshot_root", "runner", "mount_checker")
            })
        self.assertEqual(report["live_verification"], "passed")
        self.assertEqual(visited, set(identities))

    def test_live_status_detects_missing_replaced_readwrite_and_wrong_filesystem(self):
        self.pending()
        self.path.mkdir()
        self.reconcile()
        arguments = self.managed_arguments(self.runner)
        for kind in ("missing", "replaced", "readwrite", "filesystem", "unmounted"):
            with self.subTest(kind=kind):
                if kind == "missing":
                    self.path.rmdir()
                def runner(command, **kwargs):
                    result = self.runner(command, **kwargs)
                    if kind == "replaced" and command[1:3] == ["subvolume", "show"]:
                        result.stdout = "UUID: " + self.FS
                    elif kind == "readwrite" and command[1:3] == ["property", "get"]:
                        result.stdout = "ro=false"
                    elif kind == "filesystem" and command[1:3] == ["filesystem", "show"]:
                        result.stdout = "Label: none uuid: " + self.ID
                    return result
                before = {path: path.read_bytes() for path in self.directory.iterdir()}
                report = backup.live_status_report(self.state, self.manifest,
                    source=arguments["source"], snapshot_mount=self.root, snapshot_root=self.snapshots,
                    runner=runner, mount_checker=(lambda path: False) if kind == "unmounted" else arguments["mount_checker"])
                self.assertEqual(report["live_verification"], "failed")
                self.assertIn("live-snapshot-verification-failed", report["problems"])
                self.assertEqual(report["health"], "attention")
                self.assertEqual(before, {path: path.read_bytes() for path in self.directory.iterdir()})
                if kind == "missing":
                    self.path.mkdir()

    def test_nested_subvolume_refuses_capture_before_readiness(self):
        from unittest.mock import patch
        def runner(arguments, **kwargs):
            if arguments[1:3] == ["subvolume", "list"]:
                return subprocess.CompletedProcess(arguments, 0, stdout="ID 99 path nested\n")
            return self.runner(arguments, **kwargs)
        with patch.object(backup, "wait_for_management") as readiness, self.assertRaises(backup.BackupError):
            backup.perform_managed_backup(**self.managed_arguments(runner))
        readiness.assert_not_called()
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNone(state["pending_snapshot"])
        self.assertIsNone(state["last_success"])
        self.assertEqual(manifest["snapshots"], [])
        self.assertEqual(state["last_attempt"]["stage"], "preflight")

    def test_sync_failure_keeps_capture_pending_until_synced_reconciliation(self):
        from unittest.mock import patch
        restored = False
        def runner(arguments, **kwargs):
            if arguments[1:3] == ["subvolume", "snapshot"]:
                self.path.mkdir()
                return subprocess.CompletedProcess(arguments, 0)
            if arguments[1:3] == ["filesystem", "sync"]:
                self.assertTrue(restored)
                self.assertEqual(kwargs["timeout"], backup.DEFAULT_SNAPSHOT_TIMEOUT)
                raise subprocess.TimeoutExpired(arguments, kwargs["timeout"], stderr="SECRET_CANARY_SYNC")
            return self.runner(arguments, **kwargs)
        def transaction(action, **kwargs):
            nonlocal restored
            action()
            restored = True
        with patch.object(backup, "wait_for_management"), patch.object(backup, "perform_backup", side_effect=transaction), self.assertRaises(backup.BackupError) as failure:
            backup.perform_managed_backup(**self.managed_arguments(runner))
        self.assertEqual(failure.exception.reason, "sync-timeout")
        self.assertEqual(failure.exception.stage, "durability-sync")
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNotNone(state["pending_snapshot"])
        self.assertIsNone(state["last_success"])
        self.assertEqual(manifest["snapshots"], [])
        self.assertEqual(state["last_attempt"]["stage"], "durability-sync")
        self.assertNotIn("SECRET_CANARY_SYNC", json.dumps(state))
        synced = False
        def retry_runner(arguments, **kwargs):
            nonlocal synced
            if arguments[1:3] == ["filesystem", "sync"]:
                self.assertIsNone(backup.load_metadata(self.directory, self.snapshots)[0]["last_success"])
                synced = True
            return self.runner(arguments, **kwargs)
        def stop_after_reconciliation(*args, **kwargs):
            self.assertTrue(synced)
            self.assertIsNotNone(backup.load_metadata(self.directory, self.snapshots)[0]["last_success"])
            raise backup.BackupError("stop before another capture")
        with patch.object(backup, "prepare_snapshot", side_effect=stop_after_reconciliation), self.assertRaises(backup.BackupError):
            backup.perform_managed_backup(**self.managed_arguments(retry_runner))
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNone(state["pending_snapshot"])
        self.assertEqual(state["last_success"]["snapshot_path"], str(self.path))
        self.assertEqual(len(manifest["snapshots"]), 1)

    def test_failed_connection_preserves_pending_without_secret_in_health_or_cli(self):
        from unittest.mock import patch
        import contextlib
        import io
        secret = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd"
        def fail_connection():
            raise RuntimeError("Authorization: Bearer " + secret)
        args = self.managed_arguments(self.runner)
        args["connection_factory"] = fail_connection
        with patch.object(backup, "wait_for_management"), self.assertRaises(backup.BackupError):
            backup.perform_managed_backup(**args)
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNotNone(state["pending_snapshot"])
        self.assertEqual(state["last_attempt"]["result"], "failed")
        self.assertNotIn(secret, json.dumps(state))
        self.assertNotIn(secret, json.dumps(manifest))
        stderr = io.StringIO()
        with patch.object(backup.sys, "argv", ["minecraft-backup"]), patch.object(backup, "command_backup", side_effect=RuntimeError(secret)), contextlib.redirect_stderr(stderr):
            self.assertEqual(backup.main(), 1)
        self.assertNotIn(secret, stderr.getvalue())

    def test_readiness_retries_discovery_without_mutation_and_is_bounded(self):
        ticks = [0.0]
        calls = []
        def clock():
            return ticks[0]
        def sleeper(seconds):
            ticks[0] += seconds
        def unavailable():
            calls.append(ticks[0])
            raise OSError("unavailable")
        with self.assertRaises(backup.BackupError):
            backup.wait_for_management(unavailable, timeout=3, clock=clock, sleeper=sleeper)
        self.assertEqual(calls, [0, 1, 2])
        self.assertEqual(ticks[0], 3)
        websocket = FakeWebSocket([response(1, discovery()), response(2, {"started": True})])
        factory = ConnectionFactory(websocket)
        backup.wait_for_management(factory, clock=clock, sleeper=sleeper)
        self.assertEqual([r["method"] for r in websocket.sent], ["rpc.discover", "minecraft:server/status"])

    def test_readiness_permanent_failures_are_immediate_and_leave_no_intent(self):
        from unittest.mock import patch
        failures = [backup.msmp.ConfigurationError("bad config"),
                    backup.msmp.ProtocolError("missing capability"),
                    backup.msmp.RpcError({"code": -1, "message": "rejected"}),
                    ValueError("programming error")]
        for error in failures:
            with self.subTest(error=type(error).__name__):
                factory = unittest.mock.Mock(side_effect=error)
                sleeper = unittest.mock.Mock()
                with self.assertRaises(type(error)):
                    backup.wait_for_management(factory, sleeper=sleeper)
                factory.assert_called_once_with()
                sleeper.assert_not_called()
                with patch.object(backup, "wait_for_management", side_effect=error), self.assertRaises(backup.BackupError):
                    backup.perform_managed_backup(**self.managed_arguments(self.runner))
                state, manifest = backup.load_metadata(self.directory, self.snapshots)
                self.assertIsNone(state["pending_snapshot"])
                self.assertEqual(state["last_attempt"]["stage"], "readiness")
                self.assertEqual(manifest["snapshots"], [])

    def test_readiness_waits_for_real_initialization_without_mutation(self):
        from contextlib import contextmanager
        ticks = [0]
        sockets = [FakeWebSocket([response(1, discovery()), response(2, {"started": False})]),
                   FakeWebSocket([response(1, discovery()), response(2, {"started": True})])]
        calls = []
        @contextmanager
        def factory():
            ws = sockets[len(calls)]; calls.append(ws); yield ws
        backup.wait_for_management(factory, timeout=3, clock=lambda: ticks[0],
                                   sleeper=lambda value: ticks.__setitem__(0, ticks[0] + value))
        self.assertEqual(ticks[0], 1)
        self.assertEqual(len(calls), 2)
        for ws in sockets:
            self.assertEqual([r["method"] for r in ws.sent], ["rpc.discover", "minecraft:server/status"])

    def test_readiness_retries_only_exact_preinitialization_status_rpc_error(self):
        from contextlib import contextmanager
        from unittest.mock import Mock
        error = {"code": -32600, "message": "Invalid Request",
                 "data": "Method cannot be dispatched pre server initialization: minecraft:server/status"}
        first = FakeWebSocket([response(1, discovery()), {"jsonrpc": "2.0", "id": 2, "error": error}])
        second = FakeWebSocket([response(1, discovery()), response(2, {"started": True})])
        attempts = []
        @contextmanager
        def factory():
            ws = [first, second][len(attempts)]; attempts.append(ws); yield ws
        sleeper = Mock()
        backup.wait_for_management(factory, sleeper=sleeper)
        self.assertEqual(len(attempts), 2)
        sleeper.assert_called_once_with(1.0)
        for changed in [dict(error, code=-32601), dict(error, message="Forbidden"),
                        dict(error, data="Method cannot be dispatched pre server initialization: minecraft:server/save")]:
            ws = FakeWebSocket([response(1, discovery()), {"jsonrpc": "2.0", "id": 2, "error": changed}])
            sleeper = Mock()
            with self.assertRaises(backup.msmp.RpcError):
                backup.wait_for_management(ConnectionFactory(ws), sleeper=sleeper)
            sleeper.assert_not_called()

    def test_readiness_uninitialized_status_is_bounded(self):
        from contextlib import contextmanager
        ticks = [0]; attempts = []
        @contextmanager
        def factory():
            ws = FakeWebSocket([response(1, discovery()), response(2, {"started": False})])
            attempts.append(ws); yield ws
        with self.assertRaises(backup.BackupError):
            backup.wait_for_management(factory, timeout=3, clock=lambda: ticks[0],
                                       sleeper=lambda value: ticks.__setitem__(0, ticks[0]+value))
        self.assertEqual(ticks[0], 3)
        self.assertEqual(len(attempts), 3)

    def test_readiness_rejects_malformed_initialization_status_immediately(self):
        from unittest.mock import Mock
        for status in [None, True, {}, {"started": 1}, {"started": "true"}]:
            with self.subTest(status=status):
                ws = FakeWebSocket([response(1, discovery()), response(2, status)])
                sleeper = Mock()
                with self.assertRaises(backup.msmp.ProtocolError):
                    backup.wait_for_management(ConnectionFactory(ws), sleeper=sleeper)
                sleeper.assert_not_called()

    def test_readiness_refuses_missing_status_capability_without_mutation(self):
        from unittest.mock import Mock
        doc = discovery(); doc["methods"] = [m for m in doc["methods"] if m["name"] != "minecraft:server/status"]
        ws = FakeWebSocket([response(1, doc)])
        sleeper = Mock()
        with self.assertRaises(backup.msmp.ProtocolError):
            backup.wait_for_management(ConnectionFactory(ws), sleeper=sleeper)
        sleeper.assert_not_called()
        self.assertEqual([r["method"] for r in ws.sent], ["rpc.discover"])

    def test_readiness_incompatible_discovery_is_not_retried(self):
        from unittest.mock import Mock
        websocket = FakeWebSocket([response(1, {})])
        factory = ConnectionFactory(websocket)
        sleeper = Mock()
        with self.assertRaises(backup.msmp.ProtocolError):
            backup.wait_for_management(factory, sleeper=sleeper)
        sleeper.assert_not_called()
        self.assertEqual([r["method"] for r in websocket.sent], ["rpc.discover"])

    def test_readiness_authentication_rejection_is_not_retried(self):
        from unittest.mock import Mock
        from websockets.exceptions import InvalidStatus
        from websockets.http11 import Response
        error = InvalidStatus(Response(401, "Unauthorized", []))
        factory = Mock(side_effect=error)
        sleeper = Mock()
        with self.assertRaises(InvalidStatus):
            backup.wait_for_management(factory, sleeper=sleeper)
        factory.assert_called_once_with()
        sleeper.assert_not_called()

    def test_readiness_connection_close_retries(self):
        from unittest.mock import Mock
        from websockets.exceptions import ConnectionClosedError
        websocket = FakeWebSocket([response(1, discovery()), response(2, {"started": True})])
        ready = ConnectionFactory(websocket)
        calls = []
        def factory():
            calls.append(True)
            if len(calls) == 1:
                raise ConnectionClosedError(None, None)
            return ready()
        sleeper = Mock()
        backup.wait_for_management(factory, sleeper=sleeper)
        self.assertEqual(len(calls), 2)
        sleeper.assert_called_once_with(1.0)

    def test_early_mount_failure_records_current_attempt_without_capture(self):
        arguments = self.managed_arguments(self.runner)
        arguments["mount_checker"] = lambda path: False
        with self.assertRaises(backup.BackupError):
            backup.perform_managed_backup(**arguments)
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNone(state["pending_snapshot"])
        self.assertEqual(state["last_attempt"]["stage"], "environment-preflight")
        report = backup.status_report(state, manifest, recovery_marker=self.root / "absent")
        self.assertIn("last-attempt-failed", report["problems"])

    def test_readiness_timeout_precedes_pending_plan(self):
        from unittest.mock import patch
        with patch.object(backup, "wait_for_management", side_effect=backup.BackupError("timeout")), self.assertRaises(backup.BackupError):
            backup.perform_managed_backup(**self.managed_arguments(self.runner))
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNone(state["pending_snapshot"])
        self.assertEqual(state["last_attempt"]["stage"], "readiness")
        self.assertEqual(manifest["snapshots"], [])

    def test_status_freshness_and_ownership_health(self):
        self.pending()
        self.path.mkdir()
        self.reconcile()
        now = datetime(2026, 10, 11, 8, tzinfo=timezone.utc)
        report = backup.status_report(self.state, self.manifest, now, self.root / "absent-marker")
        self.assertIn("success-overdue", report["problems"])
        self.manifest["snapshots"] = []
        report = backup.status_report(self.state, self.manifest, now, self.root / "absent-marker")
        self.assertIn("last-success-not-owned", report["problems"])
        self.assertIn("established-manifest-empty", report["problems"])

    def test_status_is_read_only_and_does_not_contact_server(self):
        from unittest.mock import patch
        import contextlib
        import io
        self.pending()
        before = {path: path.read_bytes() for path in self.directory.iterdir()}
        output = io.StringIO()
        loader = backup.load_metadata
        with patch.object(backup, "load_metadata", side_effect=lambda: loader(self.directory, self.snapshots)), patch.object(backup.msmp, "open_connection", side_effect=AssertionError("status must not connect")), contextlib.redirect_stdout(output):
            backup.command_status()
        self.assertEqual(before, {path: path.read_bytes() for path in self.directory.iterdir()})
        self.assertEqual(json.loads(output.getvalue())["managed_snapshot_count"], 0)



    def test_absent_pending_path_cannot_hide_an_unsafe_parent(self):
        self.pending()
        for kind in ("mode", "symlink", "mount"):
            with self.subTest(kind=kind):
                if kind == "mode":
                    self.snapshots.chmod(0o755)
                elif kind == "symlink":
                    self.snapshots.rmdir()
                    self.snapshots.symlink_to(self.directory)
                with self.assertRaises(backup.BackupError):
                    self.reconcile(mount_checker=lambda path: kind == "mount")
                self.assertIsNotNone(backup.load_metadata(self.directory, self.snapshots)[0]["pending_snapshot"])
                if kind == "symlink":
                    self.snapshots.unlink()
                    self.snapshots.mkdir(mode=0o700)
                else:
                    self.snapshots.chmod(0o700)

    def test_status_refuses_secret_bearing_free_form_diagnostics(self):
        from unittest.mock import patch
        import contextlib
        import io
        secret = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcd"
        attempt = {"started_at": self.TIME, "finished_at": self.TIME,
                   "result": "failed", "stage": "registration", "error_type": "BackupError",
                   "message": backup.HEALTH_FAILURE_MESSAGE}
        loader = backup.load_metadata
        for field in ("stage", "error_type", "message"):
            self.state["last_attempt"] = dict(attempt, **{field: secret})
            backup.atomic_json(self.directory / "state.json", self.state)
            output, errors = io.StringIO(), io.StringIO()
            with patch.object(backup.sys, "argv", ["minecraft-backup", "status"]), patch.object(backup, "load_metadata", side_effect=lambda: loader(self.directory, self.snapshots)), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                self.assertEqual(backup.main(), 1)
            self.assertEqual(output.getvalue(), "")
            self.assertNotIn(secret, errors.getvalue())

    def test_filesystem_uuid_output_ambiguity_fails_closed(self):
        for output in ("Label: none uuid: garbage\n",
                       "Label: none uuid: 00000000-0000-0000-0000-000000000000\n",
                       "Label: none uuid: " + self.FS + "\nLabel: none uuid: invalid extra\n",
                       "Label: none uuid: " + self.FS + "\nLabel: none uuid: garbage\n",
                       "Label: none uuid: " + self.FS + "\nLabel: none uuid: " + self.FS + "\n",
                       "Label: none uuid: " + self.FS + "\nLabel: none uuid: " + self.ID + "\n"):
            def runner(arguments, **kwargs):
                return subprocess.CompletedProcess(arguments, 0, stdout=output)
            with self.subTest(output=output), self.assertRaises(backup.BackupError):
                backup.btrfs_filesystem_uuid(self.snapshots, runner=runner)

    def test_missing_established_file_and_hardlink_fail_closed(self):
        self.pending()
        self.path.mkdir()
        self.reconcile()
        state_path = self.directory / "state.json"
        saved = state_path.read_bytes()
        state_path.unlink()
        with self.assertRaises(backup.BackupError):
            backup.load_metadata(self.directory, self.snapshots)
        state_path.write_bytes(saved)
        state_path.chmod(0o600)
        os.link(state_path, self.directory / "hardlink")
        with self.assertRaises(backup.BackupError):
            backup.load_metadata(self.directory, self.snapshots)
        (self.directory / "hardlink").unlink()
        (self.directory / "managed-snapshots.json").unlink()
        with self.assertRaises(backup.BackupError):
            backup.load_metadata(self.directory, self.snapshots)

    def test_partial_temp_write_never_replaces_final(self):
        from unittest.mock import patch
        path = self.directory / "state.json"
        backup.atomic_json(path, self.state)
        before = path.read_bytes()
        def partial_write(value, stream, **kwargs):
            stream.write('{"schema_version":')
            raise OSError("injected partial write")
        with patch.object(backup.json, "dump", side_effect=partial_write):
            with self.assertRaises(OSError):
                backup.atomic_json(path, self.state)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(self.directory.glob(".minecraft-*")), [])

    def test_managed_post_capture_state_failure_keeps_durable_pending(self):
        from unittest.mock import patch
        original = backup.atomic_json
        state_writes = 0
        def writer(path, value):
            nonlocal state_writes
            if path.name == "state.json":
                state_writes += 1
                if state_writes == 2:
                    raise OSError("post-capture state write failed")
            original(path, value)
        def runner(arguments, **kwargs):
            if arguments[1:3] == ["subvolume", "snapshot"]:
                self.path.mkdir()
                return subprocess.CompletedProcess(arguments, 0)
            return self.runner(arguments, **kwargs)
        def transaction(action, **kwargs):
            return action()
        with patch.object(backup, "wait_for_management"), patch.object(backup, "atomic_json", side_effect=writer), patch.object(backup, "perform_backup", side_effect=transaction):
            with self.assertRaises(backup.BackupError):
                backup.perform_managed_backup(**self.managed_arguments(runner))
        self.state, self.manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertIsNotNone(self.state["pending_snapshot"])
        self.assertEqual(self.state["last_attempt"]["result"], "failed")
        self.assertEqual(len(self.manifest["snapshots"]), 1)
        self.reconcile()
        self.assertIsNone(backup.load_metadata(self.directory, self.snapshots)[0]["pending_snapshot"])

    def test_discovery_failure_cannot_reach_autosave_or_snapshot(self):
        websocket = FakeWebSocket([response(1, {"methods": []})])
        marker = self.root / "runtime" / "marker"
        with self.assertRaises(Exception):
            backup.perform_backup(action=lambda: self.fail("snapshot after failed discovery"),
                                  connection_factory=ConnectionFactory(websocket), recovery_marker=marker)
        self.assertEqual([request["method"] for request in websocket.sent], ["rpc.discover"])
        self.assertFalse(marker.exists())


class RetentionTests(unittest.TestCase):
    setUp = PersistentMetadataTests.setUp
    FS = PersistentMetadataTests.FS
    ID = PersistentMetadataTests.ID
    TIME = PersistentMetadataTests.TIME

    def populate(self, count):
        from datetime import timedelta
        from uuid import UUID
        self.deleted = []
        self.identities = {}
        for index in range(count):
            instant = datetime(2026, 10, 1, tzinfo=timezone.utc) + timedelta(hours=index * 6)
            path = backup.snapshot_destination(self.snapshots, instant)
            path.mkdir()
            record = {"name": path.name, "path": str(path),
                      "created_at": instant.strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "filesystem_uuid": self.FS, "subvolume_uuid": str(UUID(int=index + 1))}
            self.manifest["snapshots"].append(record)
            self.identities[str(path)] = record["subvolume_uuid"]
        backup.atomic_json(self.directory / "state.json", self.state)
        backup.atomic_json(self.directory / "managed-snapshots.json", self.manifest)

    def runner(self, arguments, **kwargs):
        self.assertTrue(kwargs["check"])
        if arguments[1:3] == ["subvolume", "delete"]:
            self.assertEqual(arguments[3], "--commit-after")
            path = Path(arguments[4])
            self.deleted.append(str(path))
            path.rmdir()
            output = ""
        elif arguments[1:3] == ["subvolume", "show"]:
            output = "UUID: " + self.identities[arguments[3]]
        elif arguments[1:3] == ["filesystem", "show"]:
            output = "Label: none uuid: " + self.FS
        elif arguments[1:3] in (["subvolume", "list"], ["filesystem", "sync"]):
            output = ""
        elif arguments[1:3] == ["property", "get"]:
            output = "ro=true"
        else:
            self.fail("unexpected command")
        return subprocess.CompletedProcess(arguments, 0, stdout=output)

    def retain(self, runner=None, mount_checker=lambda path: False):
        backup.apply_retention(self.state, self.manifest, self.directory, self.snapshots,
                               runner or self.runner, mount_checker)

    def run_capture_with_pending_deletion(self, invalid_candidate=False):
        from unittest.mock import patch
        self.populate(20)
        old_paths = [record["path"] for record in self.manifest["snapshots"]]
        self.state["pending_deletion"] = dict(self.manifest["snapshots"][0])
        backup.atomic_json(self.directory / "state.json", self.state)
        if invalid_candidate:
            self.identities[old_paths[1]] = self.FS
        events = []
        def runner(arguments, **kwargs):
            operation = arguments[1:3]
            if operation == ["subvolume", "snapshot"]:
                events.append("capture")
                self.path.mkdir()
                self.identities[str(self.path)] = self.ID
                return subprocess.CompletedProcess(arguments, 0)
            if operation == ["subvolume", "show"] and arguments[3] not in self.identities:
                return subprocess.CompletedProcess(arguments, 0, stdout="UUID: " + self.ID)
            if operation == ["subvolume", "delete"]:
                events.append("delete:" + arguments[4])
            if operation == ["filesystem", "sync"]:
                events.append("sync")
            return self.runner(arguments, **kwargs)
        def transaction(action, **kwargs):
            action()
            events.append("autosave-restored")
        arguments = PersistentMetadataTests.managed_arguments(self, runner)
        with patch.object(backup, "wait_for_management"), patch.object(backup, "perform_backup", side_effect=transaction):
            if invalid_candidate:
                with self.assertRaises(backup.BackupError):
                    backup.perform_managed_backup(**arguments)
            else:
                backup.perform_managed_backup(**arguments)
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertEqual(state["last_success"]["snapshot_path"], str(self.path))
        self.assertIsNone(state["pending_snapshot"])
        return events, old_paths, state, manifest

    def test_pending_deletion_only_precedes_capture_remaining_budget_follows(self):
        events, old_paths, state, manifest = self.run_capture_with_pending_deletion()
        self.assertEqual(events, ["delete:" + old_paths[0], "capture", "autosave-restored", "sync"]
                         + ["delete:" + path for path in old_paths[1:4]])
        self.assertEqual(len(manifest["snapshots"]), 17)
        self.assertEqual(state["last_attempt"]["result"], "success")

    def test_invalid_ordinary_retention_candidate_cannot_prevent_fresh_capture(self):
        events, old_paths, state, manifest = self.run_capture_with_pending_deletion(True)
        self.assertEqual(events, ["delete:" + old_paths[0], "capture", "autosave-restored", "sync"])
        self.assertEqual(state["last_attempt"]["stage"], "retention")
        self.assertEqual(len(manifest["snapshots"]), 20)

    def test_keep_count_and_oldest_selection_matrix(self):
        for count in (0, 1, 14, 15, 20):
            with self.subTest(count=count):
                # Isolate each count without sharing previously deleted state.
                with tempfile.TemporaryDirectory() as temporary:
                    self.directory = Path(temporary) / "state"
                    self.snapshots = Path(temporary) / "snapshots"
                    self.snapshots.mkdir(mode=0o700)
                    self.state, self.manifest = backup.load_metadata(self.directory, self.snapshots, create=True)
                    self.populate(count)
                    expected = [record["path"] for record in self.manifest["snapshots"][:min(backup.MAX_RETENTION_DELETIONS_PER_RUN, max(0, count - 14))]]
                    self.retain()
                    self.assertEqual(self.deleted, expected)
                    self.assertEqual(len(self.manifest["snapshots"]), count - len(expected))

    def test_large_backlog_continues_in_bounded_batches(self):
        self.populate(30)
        for remaining in (26, 22, 18, 14):
            before = len(self.deleted)
            self.retain()
            self.assertEqual(len(self.deleted) - before, backup.MAX_RETENTION_DELETIONS_PER_RUN)
            self.assertEqual(len(self.manifest["snapshots"]), remaining)
            durable, manifest = backup.load_metadata(self.directory, self.snapshots)
            report = backup.status_report(durable, manifest, recovery_marker=self.directory / "absent")
            self.assertEqual(report["retention_backlog_count"], max(0, remaining - 14))
            self.assertEqual("retention-backlog" in report["problems"], remaining > 14)
        self.retain()
        self.assertEqual(len(self.deleted), 16)

    def test_pending_deletion_consumes_batch_allowance(self):
        self.populate(30)
        self.state["pending_deletion"] = dict(self.manifest["snapshots"][0])
        backup.atomic_json(self.directory / "state.json", self.state)
        self.retain()
        self.assertEqual(len(self.deleted), backup.MAX_RETENTION_DELETIONS_PER_RUN)
        self.assertEqual(len(self.manifest["snapshots"]), 26)
        self.assertIsNone(self.state["pending_deletion"])

    def test_zero_remaining_budget_preserves_excess_records(self):
        self.populate(20)
        backup.apply_retention(self.state, self.manifest, self.directory, self.snapshots,
                               self.runner, lambda path: False, deletion_budget=0)
        self.assertEqual(self.deleted, [])
        self.assertEqual(len(self.manifest["snapshots"]), 20)

    def test_unknown_objects_are_ignored(self):
        self.populate(15)
        unknown = [self.snapshots / "manual", self.snapshots / "survival-20250101T000000Z"]
        for path in unknown:
            path.mkdir()
        self.retain()
        self.assertTrue(all(path.is_dir() for path in unknown))
        self.assertEqual(len(self.deleted), 1)

    def test_insecure_snapshot_root_cannot_reach_deletion(self):
        self.populate(15)
        self.snapshots.chmod(0o755)
        with self.assertRaises(backup.BackupError):
            self.retain()
        self.assertEqual(self.deleted, [])
        self.assertEqual(len(backup.load_metadata(self.directory, self.snapshots)[1]["snapshots"]), 15)

    def test_candidate_validation_failure_matrix(self):
        self.populate(15)
        first = self.manifest["snapshots"][0]
        for command, replacement in (("subvolume", "UUID: " + self.FS),
                                     ("filesystem", "Label: none uuid: " + self.ID),
                                     ("property", "ro=false")):
            def runner(arguments, **kwargs):
                result = self.runner(arguments, **kwargs)
                if arguments[1] == command:
                    result.stdout = replacement
                return result
            with self.subTest(command=command), self.assertRaises(backup.BackupError):
                self.retain(runner)
            self.assertEqual(self.deleted, [])
            self.assertTrue(Path(first["path"]).exists())
        with self.assertRaises(backup.BackupError):
            self.retain(mount_checker=lambda path: str(path) == first["path"])
        path = Path(first["path"])
        path.rmdir()
        path.symlink_to(self.directory)
        with self.assertRaises(backup.BackupError):
            self.retain()
        self.assertEqual(self.deleted, [])

    def test_delete_failure_preserves_manifest(self):
        self.populate(15)
        before = (self.directory / "managed-snapshots.json").read_bytes()
        def runner(arguments, **kwargs):
            if arguments[1:3] == ["subvolume", "delete"]:
                raise subprocess.CalledProcessError(1, arguments)
            return self.runner(arguments, **kwargs)
        with self.assertRaises(backup.BackupError):
            self.retain(runner)
        self.assertEqual((self.directory / "managed-snapshots.json").read_bytes(), before)
        self.assertEqual(backup.load_metadata(self.directory, self.snapshots)[0]["last_retention"]["result"], "failed")

    def test_deleted_before_manifest_write_reconciles_without_second_delete(self):
        from unittest.mock import patch
        self.populate(15)
        deleted_path = self.manifest["snapshots"][0]["path"]
        original = backup.atomic_json
        def fail_manifest(path, value):
            if path.name == "managed-snapshots.json":
                raise OSError("manifest failure")
            original(path, value)
        with patch.object(backup, "atomic_json", side_effect=fail_manifest):
            with self.assertRaises(backup.BackupError):
                self.retain()
        self.assertEqual(self.deleted, [deleted_path])
        self.state, self.manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertEqual(len(self.manifest["snapshots"]), 15)
        self.retain()
        self.assertEqual(self.deleted, [deleted_path])
        self.assertEqual(len(self.manifest["snapshots"]), 14)

    def test_missing_paths_without_intent_fail_closed(self):
        self.populate(15)
        before = (self.directory / "managed-snapshots.json").read_bytes()
        for record in (self.manifest["snapshots"][0], self.manifest["snapshots"][-1]):
            Path(record["path"]).rmdir()
            with self.assertRaises(backup.BackupError):
                self.retain()
            self.assertEqual(self.deleted, [])
            self.assertEqual((self.directory / "managed-snapshots.json").read_bytes(), before)

    def test_intent_is_durable_before_delete_and_retry_is_identity_checked(self):
        self.populate(15)
        first = dict(self.manifest["snapshots"][0])
        def interrupted(arguments, **kwargs):
            if arguments[1:3] == ["subvolume", "delete"]:
                durable, _ = backup.load_metadata(self.directory, self.snapshots)
                self.assertEqual(durable["pending_deletion"], first)
                raise subprocess.TimeoutExpired(arguments, 60)
            return self.runner(arguments, **kwargs)
        with self.assertRaises(backup.BackupError):
            self.retain(interrupted)
        self.state, self.manifest = backup.load_metadata(self.directory, self.snapshots)
        self.identities[first["path"]] = self.FS
        with self.assertRaises(backup.BackupError):
            self.retain()
        self.assertEqual(self.deleted, [])
        self.identities[first["path"]] = first["subvolume_uuid"]
        self.retain()
        self.assertEqual(self.deleted, [first["path"]])
        self.assertIsNone(backup.load_metadata(self.directory, self.snapshots)[0]["pending_deletion"])

    def test_manifest_updated_but_intent_clear_interrupted(self):
        from unittest.mock import patch
        self.populate(15)
        original = backup.atomic_json
        def interrupted(path, value):
            if path.name == "state.json" and value["pending_deletion"] is None:
                raise OSError("intent clear interrupted")
            original(path, value)
        with patch.object(backup, "atomic_json", side_effect=interrupted), self.assertRaises(backup.BackupError):
            self.retain()
        self.state, self.manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertEqual(len(self.manifest["snapshots"]), 14)
        self.assertIsNotNone(self.state["pending_deletion"])
        self.retain()
        self.assertEqual(len(self.deleted), 1)
        self.assertIsNone(self.state["pending_deletion"])

    def test_unexpected_loss_blocks_even_an_interrupted_deletion_retry(self):
        self.populate(16)
        self.state["pending_deletion"] = dict(self.manifest["snapshots"][0])
        backup.atomic_json(self.directory / "state.json", self.state)
        Path(self.manifest["snapshots"][-1]["path"]).rmdir()
        with self.assertRaises(backup.BackupError):
            self.retain()
        self.assertEqual(self.deleted, [])
        self.assertEqual(len(backup.load_metadata(self.directory, self.snapshots)[1]["snapshots"]), 16)

    def test_absent_deletion_intent_on_wrong_filesystem_preserves_manifest(self):
        self.populate(15)
        first = self.manifest["snapshots"][0]
        self.state["pending_deletion"] = dict(first)
        backup.atomic_json(self.directory / "state.json", self.state)
        Path(first["path"]).rmdir()
        def wrong_filesystem(arguments, **kwargs):
            result = self.runner(arguments, **kwargs)
            if arguments[1:3] == ["filesystem", "show"]:
                result.stdout = "Label: none uuid: " + self.ID
            return result
        with self.assertRaises(backup.BackupError):
            self.retain(wrong_filesystem)
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertEqual(state["pending_deletion"], first)
        self.assertIn(first, manifest["snapshots"])
        self.assertEqual(self.deleted, [])

    def test_intent_write_failure_cannot_delete(self):
        from unittest.mock import patch
        self.populate(15)
        original = backup.atomic_json
        def interrupted(path, value):
            if path.name == "state.json" and value["pending_deletion"] is not None:
                raise OSError("intent write interrupted")
            original(path, value)
        with patch.object(backup, "atomic_json", side_effect=interrupted), self.assertRaises(backup.BackupError):
            self.retain()
        self.assertEqual(self.deleted, [])

    def test_current_and_pending_are_protected(self):
        self.populate(20)
        current, pending = self.manifest["snapshots"][:2]
        self.state["last_success"] = {"created_at": current["created_at"], "snapshot_path": current["path"],
                                      "snapshot_uuid": current["subvolume_uuid"], "filesystem_uuid": self.FS}
        self.state["pending_snapshot"] = {"path": pending["path"], "planned_at": pending["created_at"],
                                          "source_filesystem_uuid": self.FS}
        backup.atomic_json(self.directory / "state.json", self.state)
        self.retain()
        self.assertEqual(len(self.deleted), 4)
        self.assertNotIn(current["path"], self.deleted)
        self.assertNotIn(pending["path"], self.deleted)
        self.assertEqual(self.manifest["snapshots"][-1]["created_at"], "2026-10-05T18:00:00Z")

    def test_retention_failure_preserves_successful_snapshot_health(self):
        self.populate(15)
        record = self.manifest["snapshots"][-1]
        self.state["last_success"] = {"created_at": record["created_at"], "snapshot_path": record["path"],
                                      "snapshot_uuid": record["subvolume_uuid"], "filesystem_uuid": self.FS}
        backup.atomic_json(self.directory / "state.json", self.state)
        def runner(arguments, **kwargs):
            if arguments[1:3] == ["subvolume", "delete"]:
                raise subprocess.TimeoutExpired(arguments, 60)
            return self.runner(arguments, **kwargs)
        with self.assertRaises(backup.BackupError):
            self.retain(runner)
        state, manifest = backup.load_metadata(self.directory, self.snapshots)
        self.assertEqual(state["last_success"]["snapshot_path"], record["path"])
        self.assertEqual(state["last_retention"]["result"], "failed")
        self.assertIn(record, manifest["snapshots"])


class DiagnosticTests(unittest.TestCase):
    def test_cli_only_prints_allowlisted_reason_and_stage_with_secret_canary(self):
        import contextlib
        import io
        from unittest.mock import patch
        canary = "SECRET_CANARY_AUTHORIZATION_BEARER_DO_NOT_PRINT"
        errors = [backup.BackupError(canary, reason=reason, stage="durability-sync")
                  for reason in backup.DIAGNOSTIC_REASONS]
        errors += [RuntimeError(canary), backup.BackupError(canary, reason=canary, stage=canary)]
        for error in errors:
            with self.subTest(type=type(error).__name__):
                output = io.StringIO()
                with patch.object(backup.sys, "argv", ["minecraft-backup"]), patch.object(backup, "command_backup", side_effect=error), contextlib.redirect_stderr(output):
                    self.assertEqual(backup.main(), 1)
                self.assertNotIn(canary, output.getvalue())
                self.assertIn("reason=", output.getvalue())

    def test_command_failure_and_timeout_are_distinguished_without_remote_text(self):
        canary = "SECRET_CANARY"
        cases = [("durability-sync", "sync"), ("consistency-transaction", "snapshot"), ("preflight", "btrfs")]
        for stage, prefix in cases:
            for error, suffix in ((subprocess.TimeoutExpired([canary], 60, stderr=canary), "timeout"),
                                  (subprocess.CalledProcessError(1, [canary], stderr=canary), "command-failed")):
                wrapped = backup.BackupError(canary)
                wrapped.__cause__ = error
                self.assertEqual(backup.diagnostic_reason(wrapped, stage), prefix + "-" + suffix)
        self.assertEqual(backup.diagnostic_reason(backup.msmp.ProtocolError(canary)), "management-incompatible")


if __name__ == "__main__":
    unittest.main(verbosity=2)
