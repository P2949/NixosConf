#!/usr/bin/env python3
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("prerequisites", os.environ["MINECRAFT_PREREQUISITES_SOURCE"])
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PrerequisiteTests(unittest.TestCase):
    def test_topology_rejection_matrix(self):
        uuid = "11111111-2222-3333-4444-555555555555"
        root = dict(fstype="btrfs", fsroot="/@root", uuid=uuid, options="rw,relatime")
        minecraft = dict(root, fsroot="/@minecraft")
        snapshots = dict(root, fsroot="/@snapshots")
        guard.validate_mounts(root, minecraft, snapshots)
        for key, value in (("fstype", "ext4"), ("fsroot", "/@root"),
                           ("uuid", "11111111-2222-3333-4444-555555555556"),
                           ("uuid", ""), ("options", "ro,relatime")):
            with self.subTest(key=key, value=value), self.assertRaises(guard.PrerequisiteError):
                guard.validate_mounts(root, dict(minecraft, **{key: value}), snapshots)
        with self.assertRaises(guard.PrerequisiteError):
            guard.validate_mounts(root, minecraft, dict(snapshots, fsroot="/@root"))

    def test_secret_permissions_format_and_link_rejections(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            directory.chmod(0o700)
            secret = directory / "minecraft-management.env"
            content = b"MINECRAFT_MANAGEMENT_SECRET=" + b"A" * 40 + b"\n"
            secret.write_bytes(content)
            secret.chmod(0o600)
            guard.validate_secret(directory, os.getuid(), os.getgid())
            for data in (b"", content + content, content + b"EXTRA=value\n",
                         content.replace(b"A", b"!", 1), content.replace(b"A", b"\xff", 1)):
                secret.write_bytes(data)
                with self.assertRaises(guard.PrerequisiteError):
                    guard.validate_secret(directory, os.getuid(), os.getgid())
            secret.write_bytes(content)
            for mode in (0o644, 0o640, 0o400):
                secret.chmod(mode)
                with self.assertRaises(guard.PrerequisiteError):
                    guard.validate_secret(directory, os.getuid(), os.getgid())
            secret.chmod(0o600)
            directory.chmod(0o750)
            with self.assertRaises(guard.PrerequisiteError):
                guard.validate_secret(directory, os.getuid(), os.getgid())
            directory.chmod(0o700)
            os.link(secret, directory / "extra-link")
            with self.assertRaises(guard.PrerequisiteError):
                guard.validate_secret(directory, os.getuid(), os.getgid())
            (directory / "extra-link").unlink()
            secret.rename(directory / "target")
            secret.symlink_to(directory / "target")
            with self.assertRaises(OSError):
                guard.validate_secret(directory, os.getuid(), os.getgid())

    def test_failure_output_never_includes_exception_or_secret(self):
        import contextlib
        import io
        output = io.StringIO()
        with patch.object(guard, "mount_record", side_effect=RuntimeError("secret-canary")), contextlib.redirect_stderr(output):
            self.assertEqual(guard.main(), 1)
        self.assertNotIn("secret-canary", output.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
