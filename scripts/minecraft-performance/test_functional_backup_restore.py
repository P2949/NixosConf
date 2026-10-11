import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from functional_backup_restore import (
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
