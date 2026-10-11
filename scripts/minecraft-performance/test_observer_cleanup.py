import os
from pathlib import Path
import tempfile
import unittest

from observe_queues import cleanup_observer, observer_directory


class ObserverCleanupTests(unittest.TestCase):
    def test_aborted_attempt_does_not_poison_same_gate_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, identity = observer_directory(root, 'a' * 64, 'catchup', (os.getuid(), os.getgid()))
            (first / 'sample.json').write_text('{}')
            (first / 'stop').touch()
            second, second_identity = observer_directory(root, 'a' * 64, 'catchup', (os.getuid(), os.getgid()))
            self.assertNotEqual(first, second)
            cleanup_observer(first, root, identity)
            cleanup_observer(second, root, second_identity)
            self.assertEqual(list(root.iterdir()), [])

    def test_unknown_entries_aliases_and_changed_identity_refuse_deletion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory, identity = observer_directory(root, 'a' * 64, 'catchup', (os.getuid(), os.getgid()))
            unexpected = directory / 'unrelated'
            unexpected.touch()
            with self.assertRaises(ValueError):
                cleanup_observer(directory, root, identity)
            self.assertTrue(unexpected.exists())
            unexpected.unlink()
            (directory / 'sample.json').symlink_to(root / 'outside')
            with self.assertRaises(ValueError):
                cleanup_observer(directory, root, identity)
            (directory / 'sample.json').unlink()
            with self.assertRaises(ValueError):
                cleanup_observer(directory, root, (identity[0], identity[1] + 1, identity[2]))


if __name__ == '__main__':
    unittest.main()
