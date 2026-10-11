from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from functional_clients import (
    COMMAND_MARKER,
    DISCONNECT_MARKER,
    PLAYER_PRESENT_MARKER,
    execute,
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

    def test_execute_hashes_evidence_only_after_lab_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'functional'
            state = {}

            class LifecycleLab:
                def __init__(self, manifest, path):
                    path.mkdir()
                    self.output = path
                    self.log = path / 'server.log'
                    self.log.write_text('server running\n')
                    self.server = path / 'world-clone/survival'
                    self.pid = 111
                    self.active = False
                    state['lab'] = self

                def start(self):
                    self.active = True

                def stop(self):
                    if self.active:
                        with self.log.open('a') as stream:
                            stream.write('server stopped\n')
                        self.active = False

                def __enter__(self):
                    return self

                def __exit__(self, *exception):
                    self.stop()

            class LifecycleClient:
                def __init__(
                    self,
                    manifest,
                    client_output,
                    profile,
                    duration,
                ):
                    self.output = client_output
                    self.pid = 222

                def __enter__(self):
                    self.output.mkdir()
                    (self.output / 'result.json').write_text(
                        json.dumps({'result': 'PASS'})
                    )
                    (self.output / 'heartbeat.json').write_text(
                        json.dumps({'connected': False, 'elapsed_seconds': 45.0})
                    )
                    (self.output / 'launcher.log').write_text(
                        'launcher finished\n'
                    )
                    return self

                def __exit__(self, *exception):
                    return None

            def fake_write_proof(
                manifest,
                gate,
                proof_path,
                evidence,
                result,
            ):
                lab = state['lab']

                self.assertFalse(lab.active)
                self.assertIn(
                    'server stopped',
                    lab.log.read_text(),
                )
                self.assertIn(
                    (lab.log, 'log'),
                    evidence,
                )

                proof_path.write_text('{}')
                return {
                    'result': result,
                    'evidence': str(proof_path),
                    'sha256': 'test-proof',
                }

            manifest = {
                'client': {},
                'baseline': {
                    'subvolume_uuid': 'test-baseline',
                },
            }

            with (
                patch(
                    'functional_clients.Lab',
                    LifecycleLab,
                ),
                patch(
                    'functional_clients.Client',
                    LifecycleClient,
                ),
                patch(
                    'functional_clients.exercise_non_dh_client',
                ),
                patch(
                    'functional_clients.maintenance.enter',
                ),
                patch(
                    'functional_clients.write_proof',
                    side_effect=fake_write_proof,
                ),
            ):
                references = execute(manifest, output)

            self.assertEqual(
                references['non_dh_client']['result'],
                'PASS',
            )
            self.assertTrue(
                (output / 'non-dh-client-reference.json').is_file()
            )
            self.assertFalse(
                (output / 'functional-acceptance.json').exists()
            )


if __name__ == '__main__':
    unittest.main()
