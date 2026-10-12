import io
import subprocess
import unittest

from server_runner import graceful_stop


class ServerRunnerTests(unittest.TestCase):
    def test_slow_save_gets_bounded_grace_and_timeout_still_fails(self):
        class Process:
            stdin = io.StringIO()

            def wait(self, timeout):
                self.timeout = timeout
                if timeout < 110:
                    raise subprocess.TimeoutExpired('java', timeout)

        process = Process()
        graceful_stop(process)
        self.assertEqual(process.stdin.getvalue(), 'stop\n')
        self.assertEqual(process.timeout, 300)

        class StuckProcess(Process):
            def wait(self, timeout):
                raise subprocess.TimeoutExpired('java', timeout)

        with self.assertRaises(subprocess.TimeoutExpired):
            graceful_stop(StuckProcess())


if __name__ == '__main__':
    unittest.main()
