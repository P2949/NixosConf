import copy
import unittest

from benchmark_c2me import collect_trial_pair, RunFailure, same_stack


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
    del accepted['server_tick_probe']
    accepted['git_sha'] = 'qualified-source'
    return base, candidate, accepted


class BenchmarkIdentityTests(unittest.TestCase):
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
