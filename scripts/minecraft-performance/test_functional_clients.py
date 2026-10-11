from pathlib import Path
import tempfile
import unittest

from functional_clients import (
    COMMAND_MARKER,
    DISCONNECT_MARKER,
    PLAYER_PRESENT_MARKER,
    exercise_non_dh_client,
    wait_for_log_since,
)


class FakeLab:
    def __init__(self, path):
        self.log = path
        self.log.write_text('server ready\n')
        self.commands = []

    def append(self, text):
        with self.log.open('a') as stream:
            stream.write(text + '\n')

    def send(self, command):
        self.commands.append(command)

        if PLAYER_PRESENT_MARKER in command:
            self.append('[Server] ' + PLAYER_PRESENT_MARKER)

        if COMMAND_MARKER in command:
            self.append('[Server] ' + COMMAND_MARKER)


class FakeClient:
    def __init__(self, lab, *, connected=True):
        self.lab = lab
        self.connected = connected
        self.waited_join = False
        self.finished = False

    def wait_joined(self):
        self.waited_join = True

    def joined(self):
        return self.connected

    def wait_finished(self):
        self.finished = True
        self.lab.append(DISCONNECT_MARKER)


class FunctionalClientTests(unittest.TestCase):
    def test_log_marker_must_be_newer_than_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'server.log'
            log.write_text(PLAYER_PRESENT_MARKER + '\n')
            offset = log.stat().st_size

            with self.assertRaises(RuntimeError):
                wait_for_log_since(
                    log,
                    PLAYER_PRESENT_MARKER,
                    offset,
                    timeout=0,
                )

    def test_non_dh_client_requires_player_action_and_clean_disconnect(self):
        with tempfile.TemporaryDirectory() as directory:
            lab = FakeLab(Path(directory) / 'server.log')
            client = FakeClient(lab)

            exercise_non_dh_client(lab, client)

            self.assertTrue(client.waited_join)
            self.assertTrue(client.finished)

            self.assertEqual(len(lab.commands), 3)

            self.assertIn(
                'execute if entity @a[name=PerfProbe,limit=1]',
                lab.commands[0],
            )
            self.assertIn(
                PLAYER_PRESENT_MARKER,
                lab.commands[0],
            )

            self.assertEqual(
                lab.commands[1],
                'gamemode spectator @a[name=PerfProbe,limit=1]',
            )

            self.assertIn(
                '@a[name=PerfProbe,gamemode=spectator,limit=1]',
                lab.commands[2],
            )
            self.assertIn(
                COMMAND_MARKER,
                lab.commands[2],
            )

    def test_disconnected_client_fails_before_server_action(self):
        with tempfile.TemporaryDirectory() as directory:
            lab = FakeLab(Path(directory) / 'server.log')
            client = FakeClient(lab, connected=False)

            with self.assertRaisesRegex(
                RuntimeError,
                'lost connection immediately after join',
            ):
                exercise_non_dh_client(lab, client)

            self.assertEqual(lab.commands, [])
            self.assertFalse(client.finished)


if __name__ == '__main__':
    unittest.main()
