import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("physical_check", os.environ["PHYSICAL_CHECK_SOURCE"])
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class PhysicalMarkerTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.cache = Path(self.scratch.name) / ".codex/shell_snapshots"
        self.cache.mkdir(parents=True)
        self.token = "test-token"
        self.leaf = "granular-impermanence-proof-" + self.token
        self.target, self.container = check.proof_target(self.cache, self.leaf)
        self.target.parent.mkdir(exist_ok=True)
        self.target.write_text(self.token)
        self.item = {"path": str(self.target), "container": str(self.container), "retained": True}

    def test_shell_snapshot_regular_file_cleanup_preserves_recovery_proof(self):
        # Reproduced with the installed Codex binary: startup skips directories
        # and deletes unrecognized regular files. Contrast the old flat marker.
        flat = self.cache / "old-flat-marker"
        flat.write_text(self.token)
        for entry in self.cache.iterdir():
            if entry.is_file():
                entry.unlink()
        self.assertFalse(flat.exists())
        self.assertEqual(check.sentinel_errors([self.item], self.token), [])

    def test_missing_or_corrupt_recovery_proof_still_fails(self):
        self.target.write_text("wrong-token")
        self.assertTrue(check.sentinel_errors([self.item], self.token))
        self.target.unlink()
        self.assertTrue(check.sentinel_errors([self.item], self.token))

    def test_normal_reset_requires_container_and_token_to_disappear(self):
        self.item["retained"] = False
        self.assertTrue(check.sentinel_errors([self.item], self.token))
        self.target.unlink()
        self.assertTrue(check.sentinel_errors([self.item], self.token))
        self.container.rmdir()
        self.assertEqual(check.sentinel_errors([self.item], self.token), [])

    def test_cleanup_removes_only_generated_file_and_empty_container(self):
        sibling = self.cache / "application.sh"
        sibling.write_text("real-application-state")
        check.remove_retained_sentinels([self.item])
        self.assertFalse(self.container.exists())
        self.assertEqual(sibling.read_text(), "real-application-state")

    def test_cleanup_does_not_recursively_remove_unexpected_state(self):
        extra = self.container / "unexpected"
        extra.write_text("keep")
        with self.assertRaises(OSError):
            check.remove_retained_sentinels([self.item])
        self.assertEqual(extra.read_text(), "keep")

    def test_malformed_container_is_rejected(self):
        self.item["container"] = str(self.cache)
        self.assertTrue(check.sentinel_errors([self.item], self.token))

    def test_existing_flat_markers_and_receipts_remain_supported(self):
        directory = Path(self.scratch.name) / "Documents"
        directory.mkdir()
        target, container = check.proof_target(directory, self.leaf)
        self.assertIsNone(container)
        target.write_text(self.token)
        item = {"path": str(target), "retained": True}
        self.assertEqual(check.sentinel_errors([item], self.token), [])
        check.remove_retained_sentinels([item])
        self.assertTrue(directory.is_dir())


if __name__ == "__main__":
    unittest.main()
