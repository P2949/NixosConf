import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from realtime_updates import exercise_landmark, require_generated_landmark


class LandmarkTests(unittest.TestCase):
    def test_unexplored_landmark_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'already-generated'):
            require_generated_landmark({})
        require_generated_landmark({'dimensions/minecraft/overworld/region/r.-1.0.mca': {
            'chunk_metadata': [{'xPos': x, 'zPos': 0, 'Status': 'minecraft:full'} for x in (-20, -19)]}})

    def test_restores_blocks_after_success_or_client_failure(self):
        for client_failure in (False, True):
            with self.subTest(client_failure=client_failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'dh-received.jsonl').write_text('')
                commands, air_checks = [], []
                class Lab:
                    log = root / 'server.log'
                    def send(self, command):
                        commands.append(command)
                        if command.endswith('minecraft:gold_block'):
                            with (root / 'dh-received.jsonl').open('a') as stream:
                                stream.write(json.dumps({'type': 'FullDataPartialUpdateMessage', 'exception_type': ''}) + '\n')
                class Client:
                    output = root
                    def wait_joined(self):
                        pass
                    def wait_finished(self):
                        if client_failure:
                            raise RuntimeError('client failed')
                with patch('realtime_updates.wait_for_log_since'), \
                     patch('realtime_updates.verify_air', side_effect=lambda lab, marker: air_checks.append(marker)), \
                     patch('realtime_updates.time.sleep'):
                    if client_failure:
                        with self.assertRaisesRegex(RuntimeError, 'client failed'):
                            exercise_landmark(Lab(), Client())
                    else:
                        result = exercise_landmark(Lab(), Client())
                        self.assertTrue(result['restored'])
                        self.assertGreater(result['partial_updates_after_mutation'], 0)
                self.assertIn('fill -320 300 0 -300 300 0 minecraft:air', commands)
                self.assertEqual(commands[-1], 'forceload remove -320 0 -300 0')
                self.assertIn('QUALIFICATION_DH_LANDMARK_RESTORED_AIR', air_checks)

    def test_old_partial_update_cannot_certify_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'dh-received.jsonl').write_text(json.dumps({'type': 'FullDataPartialUpdateMessage', 'exception_type': ''}) + '\n')
            commands = []
            lab = type('Lab', (), {'log': root / 'server.log', 'send': lambda self, command: commands.append(command)})()
            client = type('Client', (), {'output': root, 'wait_joined': lambda self: None})()
            with patch('realtime_updates.wait_for_log_since'), \
                 patch('realtime_updates.verify_air'), \
                 patch('realtime_updates.time.sleep'), \
                 patch('realtime_updates.time.monotonic', side_effect=[0, 46]):
                with self.assertRaisesRegex(RuntimeError, 'no DH partial update'):
                    exercise_landmark(lab, client)
            self.assertIn('fill -320 300 0 -300 300 0 minecraft:air', commands)
            self.assertEqual(commands[-1], 'forceload remove -320 0 -300 0')
