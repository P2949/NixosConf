import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

from server_exit import capture, verify


class ServerExitTests(unittest.TestCase):
    def test_terminal_counters_and_identity_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            group = Path(directory)
            (group / 'memory.events').write_text('high 2\nmax 0\noom 0\noom_kill 0\n')
            (group / 'memory.peak').write_text('4096\n')
            receipt = capture(SimpleNamespace(pid=123, returncode=0), group, 'invocation')
            self.assertEqual(verify(receipt, 'invocation', 123)['memory_events']['high'], 2)
            for key, value in (('invocation_id', 'other'), ('java_pid', 124), ('returncode', 1), ('memory_peak_bytes', 0)):
                with self.subTest(key=key), self.assertRaises(RuntimeError):
                    verify({**receipt, key: value}, 'invocation', 123)
            for key in ('oom', 'oom_kill', 'max'):
                with self.subTest(key=key), self.assertRaises(RuntimeError):
                    verify({**receipt, 'memory_events': {**receipt['memory_events'], key: 1}}, 'invocation', 123)
            with self.assertRaises(RuntimeError):
                verify({**receipt, 'memory_events': {'high': 0}}, 'invocation', 123)


if __name__ == '__main__':
    unittest.main()
