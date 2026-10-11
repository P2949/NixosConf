import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dh_idle_attribution as idle
from idle_metrics import pair_invalidity_reasons


class IdleTerminalTests(unittest.TestCase):
    def row(self, variant):
        return {'variant': variant, 'mode': 'clean', 'duration': 600,
                'environment_clients_absent': True, 'host_load_pass': False,
                'unrelated_host_cpu_pct': {'median': 3, 'p95': 6, 'maximum': 15}}

    def test_initial_and_three_retries_preserve_all_exact_rejections(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []
            def execute(variant, attempt):
                calls.append((variant, attempt))
                return self.row(variant)
            results, rejected, exhausted = idle.collect_pairs(root, execute, [], [])
            self.assertTrue(exhausted)
            self.assertEqual(results, [])
            self.assertEqual(calls, [(f'pair-1-{v}', a) for a in range(4) for v in ('off', 'on')])
            self.assertEqual(json.loads((root / 'rejected-pairs.json').read_text()), rejected)
            self.assertEqual(len(rejected), 4)
            for row in rejected:
                self.assertIn('off:host_p95_above_5_percent', row['invalidity_reasons'])
                self.assertIn('on:host_p95_above_5_percent', row['invalidity_reasons'])
            self.assertFalse((root / 'analysis.json').exists())
            candidate = {'git_sha': 'a' * 40}
            decision = idle.record_environment_exhaustion(root, candidate, root / 'bundle.json',
                                                         'b' * 64, results, rejected)
            progress = json.loads((root / 'progress.json').read_text())
            self.assertEqual(decision['result'], 'INCONCLUSIVE')
            self.assertEqual(progress['valid_pair_count'], 0)
            self.assertEqual(progress['rejected_attempt_count'], 4)
            self.assertEqual(progress['recovery_status'], 'PENDING')
            self.assertEqual(progress['git_sha'], candidate['git_sha'])
            self.assertEqual(progress['functional_bundle_sha256'], 'b' * 64)
            self.assertEqual(progress['reason'], 'INCONCLUSIVE_ENVIRONMENT_NOISE')
            self.assertFalse((root / 'analysis.json').exists())

    def test_every_pair_predicate_has_a_reason(self):
        off, on = self.row('off'), self.row('on')
        off.update(mode='diagnostic', duration=598, environment_clients_absent=False)
        on['unrelated_host_cpu_pct'].update(median=4, maximum=21)
        reasons = pair_invalidity_reasons(off, on)
        self.assertIn('off:mode_not_clean', reasons)
        self.assertIn('off:duration_below_599_seconds', reasons)
        self.assertIn('off:minecraft_client_overlap', reasons)
        self.assertIn('on:host_maximum_above_20_percent', reasons)
        self.assertIn('unrelated_host_median_difference_above_0_5_percentage_points', reasons)

    def test_exit_two_only_after_verified_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'maintenance.json').write_text('{}')
            idle.save(root / 'progress.json', {'final_decision': 'INCONCLUSIVE', 'recovery_status': 'PENDING'})
            def restore(output):
                self.assertEqual(json.loads((output / 'progress.json').read_text())['recovery_status'], 'PENDING')
            with patch.object(idle, 'OUTPUT', root), patch.object(idle, 'execute_main', return_value={'result': 'INCONCLUSIVE'}), patch.object(idle.signal, 'signal'), patch.object(idle.maintenance, 'restore', side_effect=restore):
                self.assertEqual(idle.main(), 2)
            self.assertEqual(json.loads((root / 'progress.json').read_text())['recovery_status'], 'PASS')
            idle.save(root / 'progress.json', {'recovery_status': 'PENDING'})
            with patch.object(idle, 'OUTPUT', root), patch.object(idle, 'execute_main', return_value={'result': 'INCONCLUSIVE'}), patch.object(idle.signal, 'signal'), patch.object(idle.maintenance, 'restore', side_effect=RuntimeError('recovery failed')):
                with self.assertRaisesRegex(RuntimeError, 'recovery failed'):
                    idle.main()
            self.assertEqual(json.loads((root / 'progress.json').read_text())['recovery_status'], 'PENDING')
