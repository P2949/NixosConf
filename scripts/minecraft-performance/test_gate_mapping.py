import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from generate_candidate_manifest import load_gate_mapping


class GateMappingTests(unittest.TestCase):
    def test_mapping_comes_from_exact_commit_and_worktree_changes_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'scripts/minecraft-performance/gate-sources.json'
            path.parent.mkdir(parents=True)
            committed = b'{"restore":["external.py"]}\n'
            path.write_bytes(committed)
            with patch('generate_candidate_manifest.subprocess.check_output', return_value=committed) as git:
                mapping, digest = load_gate_mapping(root, 'a' * 40)
                self.assertEqual(mapping, {'restore': ['external.py']})
                self.assertEqual(digest, hashlib.sha256(committed).hexdigest())
                self.assertIn('a' * 40 + ':scripts/minecraft-performance/gate-sources.json', git.call_args.args[0])
                path.write_text('{"restore":["unrelated.py"]}')
                with self.assertRaises(ValueError):
                    load_gate_mapping(root, 'a' * 40)


if __name__ == '__main__':
    unittest.main()
