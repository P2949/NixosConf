import json
from pathlib import Path
import tempfile
import unittest

from analyze_dh_idle import analyze, stacks, verified_gate, paired_mean_interval
from idle_metrics import indexed_pairs
from assemble_functional_acceptance import REQUIRED, assemble
from qualification_proof import write_proof


class IdleDecisionTests(unittest.TestCase):
    def test_authentic_functional_failure_overrides_passing_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            manifest = {'git_sha': 'a' * 40, 'baseline': {'subvolume_uuid': 'fixed'},
                        'gate_test_sources': {gate: 'source-' + gate for gate in REQUIRED}}
            evidence = root / 'functional.log'
            evidence.write_text('runtime fixture')
            refs = {gate: write_proof(manifest, gate, root / (gate + '-proof.json'),
                    [(evidence, 'log')], 'FAIL' if gate == 'backup' else 'PASS') for gate in REQUIRED}
            (root / 'candidate-manifest.json').write_text(json.dumps(manifest))
            (root / 'functional-acceptance.json').write_text(json.dumps(assemble(manifest, [refs])))
            result = analyze(root)
            self.assertEqual(result['idle_acceptance'], 'PASS')
            self.assertEqual(result['functional_gates']['backup'], 'FAIL')
            self.assertEqual(result['result'], 'FAIL')

    def test_power_requires_fixed_eleven_and_uses_paired_mean(self):
        for size in (5, 7, 9, 12):
            with self.assertRaises(ValueError):
                paired_mean_interval([1.] * size)
        values = [0.] * 10 + [11.]
        low, high = paired_mean_interval(values)
        self.assertAlmostEqual((low + high) / 2, 1.)
        self.assertLess(low, 1.)
        self.assertGreater(high, 1.)

    def test_adaptive_pairs_have_a_finite_cap_and_require_every_variant(self):
        rows = [{'variant': f'pair-{i}-{variant}', 'service_cpu_interval_one_core_pct': 1,
                 'package_power_w': 5} for i in range(1, 12) for variant in ('off', 'on')]
        for count in (5, 7, 9, 11):
            self.assertEqual(len(indexed_pairs(rows[:count * 2], count)), count)
            with self.assertRaises(ValueError):
                indexed_pairs(rows[:count * 2 - 1], count)
        for count in (0, 4, 6, 10, 12, 13):
            with self.assertRaises(ValueError):
                indexed_pairs(rows, count)
    def test_bare_pass_and_stale_proof_cannot_certify_functional_gate(self):
        self.assertEqual(verified_gate('PASS'), 'UNPROVEN')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'proof.json'
            path.write_text('{"result":"PASS"}')
            self.assertEqual(verified_gate({'result': 'PASS', 'evidence': str(path),
                                            'sha256': 'wrong'}), 'UNPROVEN')
    def fixture(self, root, delta=0.2):
        rows = []
        for i in range(1, 12):
            for variant, power, cpu in [('off', 5, .25), ('on', 5 + delta, 2)]:
                rows.append({'variant': f'pair-{i}-{variant}', 'package_power_w': power,
                             'service_cpu_median_one_core_pct': cpu,
                             'service_cpu_interval_one_core_pct': cpu,
                             'service_cpu_distribution_one_core_pct': {'p95': cpu},
                             'world_unchanged': True, 'memory_events_delta': {'oom': 0},
                             'mode': 'clean', 'duration': 600, 'environment_clients_absent': True,
                             'host_load_pass': True, 'unrelated_host_cpu_pct': {'median': 1, 'p95': 1, 'maximum': 1},
                             'io_sustained_pass': True,
                             'io_delta': {'rbytes': 0, 'wbytes': 81920, 'dbytes': 0}})
        (root / 'results.json').write_text(json.dumps(rows))

    def test_low_cpu_does_not_waive_power_cost(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, delta=2)
            result = analyze(root)
            self.assertFalse(result['resource_limits_pass'])
            self.assertEqual(result['result'], 'FAIL')

    def test_power_interval_straddling_budget_remains_inconclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            rows = json.loads((root / 'results.json').read_text())
            for row in rows:
                if row['variant'].endswith('on'):
                    index = int(row['variant'].split('-')[1])
                    row['package_power_w'] = 5 + ([.2, .4, 1, 1.5, 2] * 2 + [1])[index - 1]
            (root / 'results.json').write_text(json.dumps(rows))
            result = analyze(root)
            self.assertEqual(result['power_acceptance'], 'INCONCLUSIVE')
            self.assertEqual(result['idle_acceptance'], 'INCONCLUSIVE')
            self.assertEqual(result['statistical_design']['interim_inferential_looks'], 0)

    def test_resources_do_not_certify_functional_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            result = analyze(root)
            self.assertTrue(result['resource_limits_pass'])
            self.assertEqual(result['result'], 'INCONCLUSIVE')

    def test_blocked_native_samples_are_not_execution_cpu_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'jfr.json'
            thread = {'osThreadId': 123, 'javaName': 'socket-selector'}
            frame = {'method': {'type': {'name': 'sun/nio/ch/EPoll'}, 'name': 'wait'}}
            path.write_text(json.dumps({'recording': {'events': [{
                'type': 'jdk.NativeMethodSample', 'values': {
                    'sampledThread': thread, 'stackTrace': {'frames': [frame]}}}]}}))
            result = stacks(path)
            self.assertEqual(result['native_thread_names']['123'], 'socket-selector')
            self.assertEqual(result['inclusive_stack_sample_counts'], [])
            self.assertEqual(result['native_stack_sample_counts'][0]['samples'], 1)

    def test_periodic_cpu_work_uses_interval_average(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            rows = json.loads((root / 'results.json').read_text())
            for row in rows:
                if row['variant'].endswith('on'):
                    row['service_cpu_median_one_core_pct'] = 0
                    row['service_cpu_interval_one_core_pct'] = 6
            (root / 'results.json').write_text(json.dumps(rows))
            self.assertFalse(analyze(root)['resource_limits_pass'])

    def test_high_percentile_bursts_are_gated_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            rows = json.loads((root / 'results.json').read_text())
            for row in rows:
                if row['variant'].endswith('on'):
                    row['service_cpu_distribution_one_core_pct']['p95'] = 11
            (root / 'results.json').write_text(json.dumps(rows))
            self.assertFalse(analyze(root)['resource_limits_pass'])

    def test_duplicate_missing_and_nonfinite_pairs_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for case in ('duplicate', 'missing', 'nonfinite'):
                self.fixture(root)
                rows = json.loads((root / 'results.json').read_text())
                if case == 'duplicate':
                    rows.append(rows[0])
                elif case == 'missing':
                    rows.pop()
                else:
                    rows[0]['package_power_w'] = float('nan')
                (root / 'results.json').write_text(json.dumps(rows))
                with self.assertRaises(ValueError):
                    analyze(root)

    def test_confounded_pair_prevents_idle_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            rows = json.loads((root / 'results.json').read_text())
            rows[0]['unrelated_host_cpu_pct']['median'] = 2
            (root / 'results.json').write_text(json.dumps(rows))
            self.assertEqual(analyze(root)['idle_acceptance'], 'INCONCLUSIVE')

    def test_database_growth_pressure_and_io_cannot_be_waived(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for condition in ('world', 'memory', 'io'):
                self.fixture(root)
                rows = json.loads((root / 'results.json').read_text())
                if condition == 'world':
                    rows[1]['world_unchanged'] = False
                elif condition == 'memory':
                    rows[1]['memory_events_delta']['high'] = 1
                else:
                    rows[1]['io_delta']['wbytes'] += 100000
                (root / 'results.json').write_text(json.dumps(rows))
                self.assertEqual(analyze(root)['idle_acceptance'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
