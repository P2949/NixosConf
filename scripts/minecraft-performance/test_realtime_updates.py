from contextlib import closing
import os
import sqlite3
from types import SimpleNamespace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from realtime_updates import exercise_landmark, require_generated_landmark, qualify_realtime


class LandmarkTests(unittest.TestCase):
    def test_unexplored_landmark_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'already-generated'):
            require_generated_landmark({})
        for layout in ('region/r.-1.0.mca', 'dimensions/minecraft/overworld/region/r.-1.0.mca'):
            require_generated_landmark({layout: {
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

    def test_remaining_realtime_preconditions_and_unchanged_section_fail(self):
        from functional_dh import VERIFIED_DH_3_3_4_SHA256
        for condition in ('missing_render', 'render_reaches_landmark', 'forced_chunks', 'live_initial_client', 'unchanged_section'):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / 'evidence'
                (output / 'client-dh').mkdir(parents=True)
                server = root / 'server'
                (server / 'world').mkdir(parents=True)
                if condition == 'forced_chunks':
                    (server / 'world/chunks.dat').write_bytes(b'pre-existing')
                cache = root / 'client/instances/dh-clean/minecraft/Distant_Horizons_server_data/server/id@minecraft@@overworld/DistantHorizons.sqlite'
                cache.parent.mkdir(parents=True)
                with closing(sqlite3.connect(cache)) as connection:
                    connection.execute('CREATE TABLE FullData(DetailLevel, PosX, PosZ, DataChecksum, Data)')
                    connection.execute('INSERT INTO FullData VALUES(0,-5,0,7,?)', (b'unchanged terrain',))
                    connection.commit()
                options = '' if condition == 'missing_render' else ('renderDistance:19\n' if condition == 'render_reaches_landmark' else 'renderDistance:8\n')
                manifest = {'mods': [{'id': 'distanthorizons', 'sha256': VERIFIED_DH_3_3_4_SHA256}],
                            'client': {'root': str(root / 'client'), 'profiles': {'dh-clean': {
                                'files': {'options.txt': {'content': options}}}}}}
                lab = SimpleNamespace(server=server)
                regions = {'region/r.-1.0.mca': {'chunk_metadata': [
                    {'xPos': x, 'zPos': 0, 'Status': 'minecraft:full'} for x in (-20, -19)]}}
                starts = []
                class Client:
                    pid = 99999999
                    def __init__(self, manifest, path, profile, duration):
                        starts.append(profile)
                        path.mkdir()
                        (path / 'result.json').write_text('{"result":"PASS"}')
                        (path / 'heartbeat.json').write_text('{"connected":false,"elapsed_seconds":120}')
                        (path / 'dh-received.jsonl').write_text(json.dumps({'monotonic_ns': 1, 'type': 'FullDataPartialUpdateMessage', 'exception_type': ''}) + '\n')
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                initial_pid = os.getpid() if condition == 'live_initial_client' else 99999998
                with patch('client_runtime.Client', Client), \
                     patch('realtime_updates.exercise_landmark', return_value={'restored': True}):
                    with self.assertRaises(RuntimeError):
                        qualify_realtime(lab, manifest, output, regions, initial_pid)
                self.assertFalse((output / 'dh-realtime.json').exists())
                if condition != 'unchanged_section':
                    self.assertFalse(starts)
