from contextlib import closing
import sqlite3
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from functional_backup_restore import (
    inspect_restored_server_dh,
    exercise_restored_dh,
    parse_subvolume_identity,
    require_fresh_backup,
    replace_lab_root_with_snapshot,
    write_backup_restore_proofs,
)


def status(
    snapshot_uuid,
    snapshot_path,
    *,
    health='ok',
    live='passed',
    attempt='success',
):
    return {
        'health': health,
        'live_verification': live,
        'state': {
            'last_attempt': {
                'result': attempt,
            },
            'last_success': {
                'snapshot_uuid': snapshot_uuid,
                'filesystem_uuid': (
                    '11111111-1111-1111-1111-111111111111'
                ),
                'snapshot_path': snapshot_path,
                'created_at': '2026-10-11T12:00:00Z',
            },
        },
    }


class BackupRestoreTests(unittest.TestCase):
    def test_clone_identity_mismatch_prevents_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            root = output / 'world-clone'
            root.mkdir()
            lab = SimpleNamespace(active=False, root=root, output=output,
                manifest={'baseline': {'subvolume_uuid': 'expected-parent',
                                       'filesystem_uuid': 'expected-filesystem'}})
            for identity in (
                {'readonly': False, 'parent_uuid': 'unrelated', 'filesystem_uuid': 'expected-filesystem'},
                {'readonly': False, 'parent_uuid': 'expected-parent', 'filesystem_uuid': 'unrelated'},
                {'readonly': True, 'parent_uuid': 'expected-parent', 'filesystem_uuid': 'expected-filesystem'},
            ):
                with patch('functional_backup_restore.subvolume_identity', return_value=identity), \
                     patch('functional_backup_restore.subprocess.run') as run:
                    with self.assertRaisesRegex(RuntimeError, 'identity mismatch before deletion'):
                        replace_lab_root_with_snapshot(lab, {'path': '/.snapshots/minecraft/survival-test'})
                    run.assert_not_called()

    def test_fresh_backup_requires_new_verified_recovery_point(self):
        old = status(
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            '/.snapshots/minecraft/survival-old',
        )

        new = status(
            'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
            '/.snapshots/minecraft/survival-new',
        )

        point = require_fresh_backup(
            old,
            new,
        )

        self.assertEqual(
            point['snapshot_uuid'],
            'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        )

        with self.assertRaisesRegex(
            RuntimeError,
            'fresh recovery point',
        ):
            require_fresh_backup(
                old,
                old,
            )

        failed = status(
            'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
            '/.snapshots/minecraft/survival-new',
            attempt='failed',
        )

        with self.assertRaisesRegex(
            RuntimeError,
            'did not succeed',
        ):
            require_fresh_backup(
                old,
                failed,
            )

    def test_parse_subvolume_identity_preserves_parent_relationship(self):
        metadata = """
Name: restore
UUID: bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb
Parent UUID: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
Received UUID: -
"""

        identity = parse_subvolume_identity(
            Path('/persist/restore'),
            metadata,
            'ro=false',
            '11111111-1111-1111-1111-111111111111',
        )

        self.assertEqual(
            identity['subvolume_uuid'],
            'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        )

        self.assertEqual(
            identity['parent_uuid'],
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        )

        self.assertFalse(
            identity['readonly']
        )

    def test_proofs_require_stopped_server_and_bind_restore_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            client = output / 'client'
            client.mkdir()

            before = status(
                'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                '/.snapshots/minecraft/survival-old',
            )

            recovery = status(
                'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
                '/.snapshots/minecraft/survival-new',
            )['state']['last_success']

            (output / 'backup-before.json').write_text(
                json.dumps(before)
            )

            (
                output
                / 'pre-maintenance-backup.json'
            ).write_text(
                json.dumps(
                    status(
                        recovery['snapshot_uuid'],
                        recovery['snapshot_path'],
                    )
                )
            )

            snapshot_identity = {
                'path': recovery['snapshot_path'],
                'subvolume_uuid': recovery['snapshot_uuid'],
                'parent_uuid': (
                    'cccccccc-cccc-cccc-cccc-cccccccccccc'
                ),
                'filesystem_uuid': recovery['filesystem_uuid'],
                'readonly': True,
            }

            clone_identity = {
                'path': '/persist/restore-clone',
                'subvolume_uuid': (
                    'dddddddd-dddd-dddd-dddd-dddddddddddd'
                ),
                'parent_uuid': recovery['snapshot_uuid'],
                'filesystem_uuid': recovery['filesystem_uuid'],
                'readonly': False,
            }

            (
                output
                / 'backup-snapshot-identity.json'
            ).write_text(
                json.dumps(
                    snapshot_identity
                )
            )

            (
                output
                / 'restore-clone-identity.json'
            ).write_text(
                json.dumps(
                    clone_identity
                )
            )

            (client / 'result.json').write_text(
                json.dumps({
                    'result': 'PASS',
                })
            )

            (
                client
                / 'heartbeat.json'
            ).write_text(
                json.dumps({
                    'connected': True,
                    'elapsed_seconds': 45.0,
                })
            )

            (
                client
                / 'launcher.log'
            ).write_text(
                'launcher finished\n'
            )

            class Lab:
                active = False
                pid = 123
                server = (
                    output
                    / 'restore-lab'
                    / 'world-clone'
                    / 'survival'
                )
                log = output / 'server.log'

            Lab.log.write_text(
                'server stopped\n'
            )

            manifest = {
                'baseline': {
                    'subvolume_uuid': 'baseline',
                },
            }

            (output / 'restore-dh.json').write_text(json.dumps({'result': 'PASS', 'evidence': []}))
            calls = []

            def fake_write_proof(
                manifest,
                gate,
                path,
                evidence,
                result,
            ):
                calls.append({
                    'gate': gate,
                    'result': result,
                    'evidence': list(evidence),
                })

                path.write_text('{}')

                return {
                    'result': result,
                    'evidence': str(path),
                    'sha256': 'test-' + gate,
                }

            with patch(
                'functional_backup_restore.write_proof',
                side_effect=fake_write_proof,
            ):
                references = write_backup_restore_proofs(
                    manifest,
                    output,
                    Lab,
                    client,
                    123,
                    456,
                    before,
                    recovery,
                    snapshot_identity,
                    clone_identity,
                )

            self.assertEqual(
                set(references),
                {
                    'backup',
                    'restore',
                },
            )

            self.assertEqual(
                [call['gate'] for call in calls],
                [
                    'backup',
                    'restore',
                ],
            )

            restore_evidence = dict(
                (
                    str(path),
                    kind,
                )
                for path, kind
                in calls[1]['evidence']
            )

            self.assertIn(str(output / 'restore-dh.json'), restore_evidence)

            self.assertIn(
                str(Lab.log),
                restore_evidence,
            )

            self.assertIn(
                str(
                    output
                    / 'restore-clone-identity.json'
                ),
                restore_evidence,
            )

            self.assertTrue(
                (
                    output
                    / 'backup-restore-reference.json'
                ).is_file()
            )

            self.assertFalse(
                (
                    output
                    / 'functional-acceptance.json'
                ).exists()
            )

            Lab.active = True

            with self.assertRaisesRegex(
                RuntimeError,
                'stopped functional server',
            ):
                write_backup_restore_proofs(
                    manifest,
                    output,
                    Lab,
                    client,
                    123,
                    456,
                    before,
                    recovery,
                    snapshot_identity,
                    clone_identity,
                )


if __name__ == '__main__':
    unittest.main()


class RestoredDhRuntimeTests(unittest.TestCase):
    def database(self, path, useful=True):
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as connection:
            connection.execute('CREATE TABLE FullData(DetailLevel, PosX, PosZ, DataChecksum, Data)')
            if useful:
                connection.execute('INSERT INTO FullData VALUES(0,-5,0,7,?)', (b'restored terrain',))
                connection.commit()

    def test_snapshot_requires_useful_dh_before_boot(self):
        for condition in ('missing', 'corrupt', 'empty', 'useful'):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / 'evidence'
                output.mkdir()
                lab = SimpleNamespace(active=False, server=root / 'server')
                lab.server.mkdir()
                source = lab.server / 'world/overworld/DistantHorizons.sqlite'
                if condition == 'corrupt':
                    source.parent.mkdir(parents=True)
                    source.write_bytes(b'corrupt')
                elif condition != 'missing':
                    self.database(source, condition == 'useful')
                    self.database(lab.server / 'world/nether/DistantHorizons.sqlite', useful=False)
                if condition == 'useful':
                    summary = inspect_restored_server_dh(lab, output)
                    self.assertEqual(summary['database_count'], 2)
                    self.assertEqual(summary['useful_database_count'], 1)
                    self.assertEqual(summary['aggregate_useful_full_data_rows'], 1)
                    self.assertTrue(summary['inspected_before_server_boot'])
                    self.assertTrue(all(row['integrity'] == 'ok' for row in summary['databases']))
                else:
                    with self.assertRaises((RuntimeError, sqlite3.DatabaseError)):
                        inspect_restored_server_dh(lab, output)
                    self.assertFalse((output / 'restore-server-dh.json').exists())
                self.assertFalse(lab.active)

    def test_fresh_restored_dh_client_failure_paths_and_evidence(self):
        for condition in ('probe', 'heartbeat', 'no_response', 'corrupt_cache', 'empty_cache', 'success'):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / 'evidence'
                output.mkdir()
                lab = SimpleNamespace(output=root / 'lab', active=True)
                lab.output.mkdir()
                source = root / 'restored-server/DistantHorizons.sqlite'
                self.database(source)
                stopped = SimpleNamespace(active=False, server=source.parent)
                summary = inspect_restored_server_dh(stopped, output)
                cache = root / 'client/instances/dh-clean/minecraft/Distant_Horizons_server_data/overworld/DistantHorizons.sqlite'
                if condition == 'corrupt_cache':
                    cache.parent.mkdir(parents=True)
                    cache.write_bytes(b'corrupt')
                else:
                    self.database(cache, condition != 'empty_cache')
                assertions = self
                class Client:
                    pid = 99999999
                    def __init__(self, manifest, path, profile, duration, *, fresh_cache=False):
                        assertions.assertEqual(profile, 'dh-clean')
                        assertions.assertTrue(fresh_cache)
                        path.mkdir()
                        (path / 'result.json').write_text(json.dumps({'result': 'FAIL' if condition == 'probe' else 'PASS'}))
                        (path / 'heartbeat.json').write_text(json.dumps({'connected': False, 'elapsed_seconds': True if condition == 'heartbeat' else 60.0}))
                        (path / 'launcher.log').write_text('clean client fixture')
                        message = {'monotonic_ns': 1, 'type': 'SessionConfigMessage' if condition == 'no_response' else 'FullDataSourceResponseMessage', 'exception_type': ''}
                        (path / 'dh-received.jsonl').write_text(json.dumps(message) + '\n')
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                manifest = {'client': {'root': str(root / 'client')}}
                with patch('functional_backup_restore.Client', Client), patch('functional_backup_restore.exercise_dh_client'):
                    if condition != 'success':
                        with self.assertRaises((RuntimeError, sqlite3.DatabaseError)):
                            exercise_restored_dh(lab, manifest, output, summary)
                        self.assertFalse((output / 'restore-dh.json').exists())
                    else:
                        receipt = exercise_restored_dh(lab, manifest, output, summary)
                        self.assertEqual(receipt['result'], 'PASS')
                        self.assertGreater(receipt['preboot_server_data']['aggregate_useful_full_data_rows'], 0)
                        bound = {entry['path'] for entry in receipt['evidence']}
                        client_output = lab.output / 'client-restore-dh'
                        for filename in ('result.json', 'heartbeat.json', 'dh-received.jsonl', 'launcher.log'):
                            self.assertIn(str(client_output / filename), bound)
                        for database in receipt['server_databases'] + receipt['client_databases']:
                            self.assertIn(database['copy'], bound)
                        self.assertIn(str(output / 'restore-server-dh.json'), bound)
