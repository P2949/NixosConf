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
                    return 'inactive'
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


if __name__ == '__main__':
    unittest.main()
