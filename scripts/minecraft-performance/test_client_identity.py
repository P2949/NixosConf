from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from client_identity import general_settings, verify
from qualification_manifest import sha256


class ClientIdentityTests(unittest.TestCase):
    def test_runtime_counters_excluded_but_collector_and_heap_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'instance.cfg'
            path.write_text('[General]\nJvmArgs=-XX:+UseZGC\nMaxMemAlloc=8192\nlastLaunchTime=1\n'
                            '[UI]\nwindow=private-ui-state\n')
            before = general_settings(path)
            path.write_text(path.read_text().replace('lastLaunchTime=1', 'lastLaunchTime=999'))
            self.assertEqual(before, general_settings(path))
            path.write_text(path.read_text().replace('UseZGC', 'UseG1GC'))
            self.assertNotEqual(before, general_settings(path))
            self.assertNotIn('window', before)

    def test_changed_client_artifact_fails_before_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instance = root / 'instances/no-dh'
            instance.mkdir(parents=True)
            (root / 'prismlauncher.cfg').write_text('[General]\nJavaPath=/fixed/java\n')
            (instance / 'instance.cfg').write_text('[General]\nJvmArgs=-XX:+UseZGC\n')
            artifact = root / 'artifact.jar'
            artifact.write_bytes(b'original')
            entry = {'path': str(artifact), 'sha256': sha256(artifact)}
            identity = {'root': str(root), 'java': {'path': '/fixed/java', 'sha256': 'fixed'},
                        'launcher': entry, 'libraries': [], 'profiles': {'no-dh': {
                            'settings': general_settings(instance / 'instance.cfg'),
                            'pack': entry, 'mods': [], 'files': {}}}}
            artifact.write_bytes(b'modified')
            def digest(path):
                return 'fixed' if str(path) == '/fixed/java' else sha256(path)
            with patch('client_identity.controlled_path', side_effect=lambda path, *a, **k: Path(path)), \
                 patch('client_identity.sha256', side_effect=digest):
                with self.assertRaisesRegex(ValueError, 'artifact changed'):
                    verify(identity, 'no-dh')


if __name__ == '__main__':
    unittest.main()
