"""Reject ambiguous or unsafe deployment policy before any operation."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from minecraft_tools.config import load_config


POLICY = {
    "schemaVersion": 1,
    "source": "/srv/game",
    "snapshotMount": "/snapshots",
    "snapshotRoot": "/snapshots/game",
    "stateDirectory": "/state/game",
    "runtimeDirectory": "/run/game",
    "management": {"host": "127.0.0.1", "port": 25585, "environmentFile": "/secrets/game.env"},
    "retention": {"snapshots": 14},
    "btrfs": {"sourceRoot": "/@game", "snapshotRoot": "/@snapshots"},
}


class ConfigTests(unittest.TestCase):
    def load(self, policy):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(policy))
            return load_config(path)

    def test_valid_policy_and_ipv6(self):
        config = self.load(POLICY)
        self.assertEqual(config.source, Path("/srv/game"))
        self.assertEqual(config.management_url, "ws://127.0.0.1:25585")
        policy = copy.deepcopy(POLICY)
        policy["management"]["host"] = "::1"
        self.assertEqual(self.load(policy).management_url, "ws://[::1]:25585")

    def test_invalid_policy_fails_closed(self):
        changes = [
            ("schemaVersion", True), ("schemaVersion", 2), ("source", "/"),
            ("source", "relative"), ("source", "/srv/../game"),
            ("snapshotRoot", "/other/game"), ("runtimeDirectory", "/state/game/run"),
            ("management", dict(POLICY["management"], port=True)),
            ("management", dict(POLICY["management"], port=65536)),
            ("management", dict(POLICY["management"], host="0.0.0.0")),
            ("management", dict(POLICY["management"], secret="forbidden")),
            ("retention", {"snapshots": 0}),
        ]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                policy = copy.deepcopy(POLICY)
                policy[key] = value
                with self.assertRaises(ValueError):
                    self.load(policy)
        for key in POLICY:
            policy = copy.deepcopy(POLICY)
            del policy[key]
            with self.assertRaises(ValueError):
                self.load(policy)

    def test_duplicate_json_field_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text('{"schemaVersion":1,"schemaVersion":1}')
            with self.assertRaises(ValueError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
