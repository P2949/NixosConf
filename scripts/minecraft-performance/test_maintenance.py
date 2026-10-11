import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import maintenance


class MaintenanceTests(unittest.TestCase):
    def test_guard_is_installed_before_any_stop_and_backup_failure_stops_nothing(self):
        for healthy in (True, False):
            with tempfile.TemporaryDirectory() as directory:
                actions = []
                def call(*args):
                    if args[0] == 'minecraft-backup':
                        return json.dumps({'health': 'ok' if healthy else 'failed',
                            'live_verification': 'passed', 'state': {'last_success': {
                                'snapshot_uuid': 'snapshot', 'filesystem_uuid': 'filesystem',
                                'snapshot_path': '/.snapshots/minecraft/verified'}}})
                    return 'not-found' if 'LoadState' in args else 'inactive'
                with patch.object(maintenance, 'call', side_effect=call), \
                     patch.object(maintenance, 'arm', side_effect=lambda output: actions.append(('arm',))), \
                     patch.object(maintenance.subprocess, 'run', side_effect=lambda args, **kwargs: actions.append(tuple(args))):
                    if healthy:
                        maintenance.enter(Path(directory))
                        guard_index = actions.index(('arm',))
                        stops = [i for i, args in enumerate(actions) if args[:2] == ('systemctl', 'stop')]
                        self.assertTrue(stops)
                        self.assertTrue(all(index > guard_index for index in stops))
                    else:
                        with self.assertRaises(RuntimeError):
                            maintenance.enter(Path(directory))
                        self.assertFalse(any(args[:2] == ('systemctl', 'stop') for args in actions))

    def test_restore_handles_unloaded_lab_and_requires_live_backup_health(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            safe = str(Path('/run/current-system').resolve())
            (output / 'maintenance.json').write_text(json.dumps({'safe_system': safe}))
            def call(*args):
                if args[0] == 'minecraft-backup':
                    return '{"health":"failed"}'
                if 'LoadState' in args:
                    return 'not-found'
                return 'active'
            with patch.object(maintenance, 'call', side_effect=call), \
                 patch.object(maintenance, 'cleanup_slice'), \
                 patch.object(maintenance.subprocess, 'run') as run:
                with self.assertRaises(RuntimeError):
                    maintenance.restore(output)
                self.assertFalse(any(list(call.args[0]) == ['systemctl', 'stop', maintenance.LAB]
                                     for call in run.call_args_list))


    def test_cleanup_failures_do_not_block_production_recovery(self):
        for stage in ('show', 'stop', 'slice', 'manifest'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                (output / 'maintenance.json').write_text(json.dumps({
                    'safe_system': str(Path('/run/current-system').resolve()),
                    'manifest_sha256': 'bound-before-mutation' if stage == 'manifest' else None,
                }))
                if stage == 'manifest':
                    (output / 'candidate-manifest.json').write_text('{}')
                actions = []
                def call(*args):
                    actions.append(args)
                    if args[0] == 'minecraft-backup':
                        return '{"health":"ok","live_verification":"passed"}'
                    if 'LoadState' in args:
                        if stage == 'show':
                            raise RuntimeError('show failed')
                        return 'loaded' if stage == 'stop' else 'not-found'
                    return 'active'
                def run(args, **kwargs):
                    actions.append(tuple(args))
                    if stage == 'stop' and args[:2] == ['systemctl', 'stop']:
                        raise RuntimeError('stop failed')
                with patch.object(maintenance, 'call', side_effect=call), \
                     patch.object(maintenance.subprocess, 'run', side_effect=run), \
                     patch.object(maintenance, 'cleanup_slice', side_effect=RuntimeError('foreign slice retained') if stage == 'slice' else None), \
                     patch.object(maintenance, 'restore_client_inputs') as client:
                    with self.assertRaisesRegex(RuntimeError, 'after production recovery'):
                        maintenance.restore(output)
                    if stage in ('manifest', 'show', 'stop'):
                        client.assert_not_called()
                self.assertIn(('systemctl', 'start', 'minecraft-server-survival.service', 'minecraft-backup.timer'), actions)
                self.assertIn(('minecraft-backup', 'status', '--live'), actions)
                self.assertTrue((output / 'recovery-status.json').exists())
                self.assertTrue(json.loads((output / 'recovery-cleanup-errors.json').read_text()))

    def test_recovery_restores_frozen_client_inputs_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            persist = base / 'persist'
            output = base / 'functional'
            root = persist / 'minecraft-performance-client-test'

            persist.mkdir()
            output.mkdir()

            profiles = {}

            for name in ('dh-clean', 'no-dh'):
                instance = root / 'instances' / name
                game = instance / 'minecraft'

                (game / 'config').mkdir(parents=True)

                pack = instance / 'mmc-pack.json'
                options = game / 'options.txt'
                dh_config = game / 'config/DistantHorizons.toml'

                pack.write_text('mutated pack\n')
                options.write_text('mutated options\n')
                dh_config.write_text('mutated dh\n')

                pack.chmod(0o644)
                options.chmod(0o644)
                dh_config.chmod(0o644)

                profiles[name] = {
                    'pack': {
                        'path': str(pack),
                        'content': f'frozen {name} pack\n',
                    },
                    'files': {
                        'options.txt': {
                            'content': f'frozen {name} options\n',
                        },
                        'config/DistantHorizons.toml': {
                            'content': f'frozen {name} dh\n',
                        },
                    },
                }

            manifest = {
                'client': {
                    'root': str(root),
                    'profiles': profiles,
                },
            }

            (output / 'candidate-manifest.json').write_text(
                json.dumps(manifest)
            )

            before = {}

            for name in ('dh-clean', 'no-dh'):
                instance = root / 'instances' / name

                for relative in (
                    'mmc-pack.json',
                    'minecraft/options.txt',
                    'minecraft/config/DistantHorizons.toml',
                ):
                    target = instance / relative
                    info = target.stat()

                    before[(name, relative)] = (
                        info.st_uid,
                        info.st_gid,
                        info.st_mode & 0o777,
                    )

            maintenance.restore_client_inputs(
                output,
                persist,
            )

            for name in ('dh-clean', 'no-dh'):
                instance = root / 'instances' / name

                self.assertEqual(
                    (instance / 'mmc-pack.json').read_text(),
                    f'frozen {name} pack\n',
                )
                self.assertEqual(
                    (instance / 'minecraft/options.txt').read_text(),
                    f'frozen {name} options\n',
                )
                self.assertEqual(
                    (
                        instance
                        / 'minecraft/config/DistantHorizons.toml'
                    ).read_text(),
                    f'frozen {name} dh\n',
                )

                for relative in (
                    'mmc-pack.json',
                    'minecraft/options.txt',
                    'minecraft/config/DistantHorizons.toml',
                ):
                    target = instance / relative
                    info = target.stat()

                    self.assertEqual(
                        (
                            info.st_uid,
                            info.st_gid,
                            info.st_mode & 0o777,
                        ),
                        before[(name, relative)],
                    )

                    self.assertFalse(
                        target.with_name(
                            target.name
                            + '.qualification-restore-tmp'
                        ).exists()
                    )

    def test_recovery_refuses_symlinked_client_target(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            persist = base / 'persist'
            output = base / 'functional'
            root = persist / 'minecraft-performance-client-test'

            persist.mkdir()
            output.mkdir()

            outside = base / 'outside-pack.json'
            outside.write_text('outside\n')

            profiles = {}

            for name in ('dh-clean', 'no-dh'):
                instance = root / 'instances' / name
                game = instance / 'minecraft'

                game.mkdir(parents=True)

                pack = instance / 'mmc-pack.json'

                if name == 'no-dh':
                    pack.symlink_to(outside)
                else:
                    pack.write_text('mutated\n')

                profiles[name] = {
                    'pack': {
                        'path': str(pack),
                        'content': 'frozen\n',
                    },
                    'files': {},
                }

            (output / 'candidate-manifest.json').write_text(
                json.dumps({
                    'client': {
                        'root': str(root),
                        'profiles': profiles,
                    },
                })
            )

            with self.assertRaisesRegex(
                RuntimeError,
                'restoration target is unsafe',
            ):
                maintenance.restore_client_inputs(
                    output,
                    persist,
                )

            self.assertEqual(
                outside.read_text(),
                'outside\n',
            )


    def test_client_fixture_failure_cannot_block_production_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)

            safe = str(
                Path('/run/current-system').resolve()
            )

            (output / 'maintenance.json').write_text(
                json.dumps({
                    'safe_system': safe,
                })
            )

            actions = []

            def call(*args):
                if args[0] == 'minecraft-backup':
                    return json.dumps({
                        'health': 'ok',
                        'live_verification': 'passed',
                    })

                if 'LoadState' in args:
                    return 'not-found'

                if (
                    args[:2]
                    == (
                        'systemctl',
                        'is-active',
                    )
                ):
                    return 'active'

                return 'inactive'

            def run(args, **kwargs):
                actions.append(tuple(args))

            with (
                patch.object(
                    maintenance,
                    'call',
                    side_effect=call,
                ),
                patch.object(
                    maintenance,
                    'restore_client_inputs',
                    side_effect=RuntimeError(
                        'fixture failure'
                    ),
                ),
                patch.object(
                    maintenance,
                    'cleanup_slice',
                ),
                patch.object(
                    maintenance.subprocess,
                    'run',
                    side_effect=run,
                ),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    'disposable client input restoration failed',
                ):
                    maintenance.restore(output)

            self.assertIn(
                (
                    'systemctl',
                    'start',
                    'minecraft-server-survival.service',
                    'minecraft-backup.timer',
                ),
                actions,
            )

            self.assertTrue(
                (output / 'recovery-status.json').is_file()
            )

            status = json.loads(
                (
                    output
                    / 'recovery-status.json'
                ).read_text()
            )

            self.assertEqual(
                status['health'],
                'ok',
            )

            self.assertEqual(
                status['live_verification'],
                'passed',
            )


if __name__ == '__main__':
    unittest.main()
