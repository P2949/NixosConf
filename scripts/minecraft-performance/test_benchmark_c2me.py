import copy
import unittest
from pathlib import Path
import subprocess
import sys

from benchmark_c2me import collect_trial_pair, pilot_decision, RunFailure, same_stack, trial_directory


def manifests():
    base = {'git_sha': 'head', 'java': {}, 'wrapper': {}, 'jvm_flags': ['-XX:+UseG1GC'],
            'service': {}, 'baseline': {}, 'client': {}, 'controlled_server_properties': {},
            'server_tick_probe': {'path': 'probe', 'sha256': 'digest'}, 'generation_bounds': {},
            'mods': [{'id': 'distanthorizons'}], 'pregen_mods': [{'id': 'chunky'}],
            'policies': {'config/DistantHorizons.toml': {}}, 'pregen_policy': {}, 'pregen_pause_seconds': -1}
    candidate = copy.deepcopy(base)
    for name in ('mods', 'pregen_mods'):
        candidate[name].append({'id': 'c2me'})
    candidate['policies']['config/c2me.toml'] = {}
    accepted = copy.deepcopy(candidate)
    accepted['git_sha'] = 'qualified-source'
    return base, candidate, accepted


class BenchmarkIdentityTests(unittest.TestCase):
    def test_pilot_never_selects_c2me_or_certifies_comparison(self):
        row = dict(correctness='PASS', valid=True, severe_memory_high=False,
                   memory_events=dict(oom=0, oom_kill=0, max=0),
                   metrics=dict(worldgen_completion_seconds=120))
        result = pilot_decision(row)
        self.assertEqual(result['result'], 'INCONCLUSIVE')
        self.assertEqual(result['pilot_outcome'], 'PASS')
        self.assertIsNone(result['decision'])
        row['correctness'] = 'INCONCLUSIVE'
        self.assertEqual(pilot_decision(row)['pilot_outcome'], 'INCONCLUSIVE')
        row['correctness'] = 'PASS'
        row['memory_events']['max'] = 1
        self.assertEqual(pilot_decision(row)['result'], 'FAIL')

    def test_console_bridge_rejects_overlong_path_before_launch(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('server_runner.py')),
            '--console', '/persist/' + 'x' * 110, '/bin/true'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('UNIX socket path limit', result.stderr)

    def test_every_trial_socket_fits_linux_limit_and_names_are_unique(self):
        study = Path('/persist/minecraft-performance-functional-c2me-study-' + 'a' * 20)
        names = set()
        for workload in ('steady', 'worldgen', 'contention'):
            for pair in range(5):
                for attempt in range(4):
                    for variant in ('without_C2ME', 'C2ME_4'):
                        path = trial_directory(study, workload, pair, attempt, variant)
                        self.assertLess(len(str(path / 'world-clone/console.sock').encode()), 108)
                        self.assertNotIn(path, names)
                        names.add(path)
        with self.assertRaises(ValueError):
            trial_directory(Path(str(study) + 'x'), 'steady', 0, 0, 'C2ME_4')

    def test_only_c2me_and_recording_instrumentation_may_differ(self):
        same_stack(*manifests())

    def test_changed_baseline_client_java_flags_and_non_c2me_rejected(self):
        for key in ('baseline', 'client', 'java', 'jvm_flags', 'server_tick_probe'):
            control, candidate, accepted = manifests()
            candidate[key] = 'changed'
            with self.subTest(key=key), self.assertRaises(ValueError):
                same_stack(control, candidate, accepted)
        control, candidate, accepted = manifests()
        candidate['mods'][0]['id'] = 'unqualified-mod'
        with self.assertRaises(ValueError):
            same_stack(control, candidate, accepted)

    def test_runtime_identical_older_correctness_source_rejected(self):
        for field in ('gate_source_mapping_sha256', 'gate_test_sources',
                      'gate_source_files', 'tool_source_files', 'server_tick_probe',
                      'generation_bounds'):
            control, candidate, accepted = manifests()
            accepted[field] = {'older': 'identity'}
            with self.subTest(field=field), self.assertRaises(ValueError):
                same_stack(control, candidate, accepted)

    def test_changed_qualified_policy_rejected(self):
        control, candidate, accepted = manifests()
        accepted['pregen_policy'] = {'changed': True}
        with self.assertRaises(ValueError):
            same_stack(control, candidate, accepted)

    def test_uninstrumented_or_non_g1_trials_rejected(self):
        control, candidate, accepted = manifests()
        for manifest in (control, candidate, accepted):
            manifest['jvm_flags'] = ['-XX:+UseZGC']
        with self.assertRaises(ValueError):
            same_stack(control, candidate, accepted)

    def test_environment_retry_is_bounded_and_order_alternates(self):
        calls = []
        results = []
        def execute(workload, pair, attempt, variant):
            calls.append((attempt, variant))
            return {'variant': variant, 'valid': False, 'invalid_reason': 'unrelated_host_load',
                    'memory_events': {}, 'severe_memory_high': False}
        self.assertEqual(collect_trial_pair('steady', 0, execute, results), 'environment_retries_exhausted')
        self.assertEqual(len(results), 8)
        self.assertEqual(calls[:4], [(0, 'without_C2ME'), (0, 'C2ME_4'),
                                    (1, 'C2ME_4'), (1, 'without_C2ME')])

    def test_unrepresentative_workload_and_resource_failure_are_not_retried(self):
        calls = []
        def execute(workload, pair, attempt, variant):
            calls.append(variant)
            return {'variant': variant, 'valid': False,
                    'invalid_reason': 'generation_shorter_than_fixed_client_window',
                    'memory_events': {}, 'severe_memory_high': False}
        self.assertEqual(collect_trial_pair('contention', 0, execute, []), 'workload_window_not_representative')
        self.assertEqual(len(calls), 2)
        def unsafe(*args):
            return {'variant': args[-1], 'valid': True, 'memory_events': {'oom': 1}, 'severe_memory_high': False}
        with self.assertRaises(RunFailure):
            collect_trial_pair('steady', 0, unsafe, [])


if __name__ == '__main__':
    unittest.main()
