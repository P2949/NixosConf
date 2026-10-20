import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("helper", os.environ["GPU_HELPER_SOURCE"])
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "state"
        self.current = "Stock"
        self.writes = []
        self.owner = {"boot": "test-boot", "daemons": [[42, "100"]]}

    def query(self, command, args):
        self.assertEqual(command, "list_profiles")
        return {"current_profile": self.current, "auto_switch": False,
                "profiles": {"Daily": None, "Stock": None}}

    def choose(self, profile):
        self.writes.append(profile)
        self.current = profile

    def action(self, operation, choose=None):
        helper.transition(operation, self.directory, self.query, choose or self.choose, self.owner)

    def test_stock_roundtrip_and_duplicate_callbacks(self):
        self.action("start")
        self.action("start")
        self.assertEqual(self.current, "Daily")
        self.action("end")
        self.action("end")
        self.assertEqual(self.current, "Stock")
        self.assertEqual(self.writes, ["Daily", "Stock"])

    def test_daily_is_a_noop_and_stale_owner_is_not_restored(self):
        self.current = "Daily"
        self.action("start")
        self.action("end")
        self.assertEqual(self.writes, [])
        self.current = "Stock"
        self.action("start")
        self.owner["boot"] = "different-boot"
        self.action("end")
        self.assertEqual(self.current, "Daily")
        self.assertFalse((self.directory / "state.json").exists())

    def test_default_roundtrip(self):
        self.current = None
        self.action("start")
        self.action("end")
        self.assertIsNone(self.current)
        self.assertEqual(self.writes, ["Daily", None])

    def test_external_profile_selection_is_preserved(self):
        self.action("start")
        self.current = "ManuallySelected"
        self.action("end")
        self.assertEqual(self.current, "ManuallySelected")
        self.assertEqual(self.writes, ["Daily"])

    def test_failed_lact_keeps_recovery_state_and_propagates_failure(self):
        def unavailable(_profile):
            raise RuntimeError("LACT unavailable")
        with self.assertRaisesRegex(RuntimeError, "unavailable"):
            self.action("start", unavailable)
        self.assertEqual(self.current, "Stock")
        self.assertTrue((self.directory / "state.json").exists())
        self.action("end")
        self.assertEqual(self.writes, [])
        self.assertFalse((self.directory / "state.json").exists())


if __name__ == "__main__":
    unittest.main()
