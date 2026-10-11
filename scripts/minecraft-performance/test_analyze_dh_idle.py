import json
from pathlib import Path
import tempfile
import unittest

from analyze_dh_idle import analyze, stacks


class IdleDecisionTests(unittest.TestCase):
    def fixture(self, root, delta=0.2):
        rows = []
        for i in range(1, 6):
            for variant, power, cpu in [('off', 5, .25), ('on', 5 + delta, 2)]:
                rows.append({'variant': f'pair-{i}-{variant}', 'package_power_w': power,
                             'service_cpu_median_one_core_pct': cpu,
                             'world_unchanged': True, 'memory_events_delta': {'oom': 0}})
        (root / 'results.json').write_text(json.dumps(rows))

    def test_low_cpu_does_not_waive_power_cost(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, delta=2)
            result = analyze(root)
            self.assertFalse(result['resource_limits_pass'])
            self.assertEqual(result['result'], 'INCONCLUSIVE')

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


if __name__ == '__main__':
    unittest.main()
