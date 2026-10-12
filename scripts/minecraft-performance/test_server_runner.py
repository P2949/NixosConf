import io
import subprocess
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from server_runner import graceful_stop, read_frame, cleanup, force_stop, MAX_COMMAND_BYTES


class ServerRunnerTests(unittest.TestCase):
    def test_fragmented_commands_and_ack(self):
        for parts, expected in (([b'sa', b'y hello', b'\n', b''], b'say hello'),
                                ([b'QU', b'EUE', b'D\n', b''], b'QUEUED'),
                                ([b'x' * MAX_COMMAND_BYTES, b'\n', b''],
                                 b'x' * MAX_COMMAND_BYTES)):
            connection = Mock()
            connection.recv.side_effect = parts
            self.assertEqual(read_frame(connection, MAX_COMMAND_BYTES), expected)

    def test_invalid_frames(self):
        for parts in ([b'stop', b''], [b'stop\nsay x\n', b''],
                      [b'\xff\n', b''], [b'\n', b''], [b'x\r\n', b''],
                      [b'x' * (MAX_COMMAND_BYTES + 1), b'\n']):
            connection = Mock()
            connection.recv.side_effect = parts
            with self.subTest(parts=str(parts)[:50]), self.assertRaises((ValueError, UnicodeError)):
                read_frame(connection, MAX_COMMAND_BYTES)

    def test_sigterm_timeout_kills_and_cleanup_always_runs(self):
        process = Mock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired('java', 15), 0]
        force_stop(process)
        process.kill.assert_called_once()
        self.assertEqual(process.wait.call_count, 2)
        listener, console = Mock(), Mock(spec=Path)
        with patch('server_runner.force_stop', side_effect=RuntimeError('kill failed')), \
                patch('server_exit.write_receipt') as receipt:
            with self.assertRaises(RuntimeError):
                cleanup(process, listener, console, Path('/private/exit.json'))
            listener.close.assert_called_once()
            console.unlink.assert_called_once_with(missing_ok=True)
            receipt.assert_called_once()

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
