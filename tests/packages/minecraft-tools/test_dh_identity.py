import tempfile
import unittest
from pathlib import Path

from minecraft_tools import dh_identity as identity


class IdentityTests(unittest.TestCase):
    def test_capture_replace_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "DistantHorizons.toml"
            saved = Path(directory) / "server-id"
            config.write_text("[server]\nserverId = -12345\n")
            identity.capture(config, saved)
            config.write_text("[server]\nsynchronizeOnLoad = true\n")
            identity.apply(config, saved)
            self.assertIn("serverId = -12345", config.read_text())
            identity.capture(config, saved)
            self.assertEqual(saved.read_text(), "-12345\n")
            self.assertEqual(saved.stat().st_mode & 0o777, 0o600)

    def test_stale_temporary_does_not_block_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            config, saved = Path(directory) / "config", Path(directory) / "id"
            stale = saved.with_suffix(".tmp")
            stale.write_text("interrupted capture")
            config.write_text("[server]\nserverId = 42\n")
            identity.capture(config, saved)
            self.assertEqual(saved.read_text(), "42\n")
            self.assertEqual(stale.read_text(), "interrupted capture")
            self.assertEqual(list(saved.parent.glob("id.*.tmp")), [])

    def test_changed_identity_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            config, saved = Path(directory) / "config", Path(directory) / "id"
            config.write_text("[server]\nserverId = 2\n")
            saved.write_text("1\n")
            with self.assertRaises(ValueError):
                identity.capture(config, saved)
            self.assertEqual(saved.read_text(), "1\n")

    def test_initial_start(self):
        with tempfile.TemporaryDirectory() as directory:
            config, saved = Path(directory) / "config", Path(directory) / "id"
            config.write_text("[server]\nsynchronizeOnLoad = true\n")
            identity.capture(config, saved)
            identity.apply(config, saved)
            self.assertFalse(saved.exists())

    def test_invalid_identity(self):
        for value in (True, "123", 2**31, -(2**31) - 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                identity.validate(value)


if __name__ == "__main__":
    unittest.main()
