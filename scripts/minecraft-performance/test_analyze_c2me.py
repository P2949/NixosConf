import unittest

from analyze_c2me import WORKLOADS, decide


def series():
    rows = []
    for workload in WORKLOADS:
        for pair in range(5):
            variants = ('without_C2ME', 'C2ME_4') if pair % 2 == 0 else ('C2ME_4', 'without_C2ME')
            for variant in variants:
                identity = f'{workload}-{pair}-{variant}'
                rows.append({'variant': variant, 'workload': workload,
                    'run_id': identity, 'clone_uuid': identity, 'valid': True,
                    'correctness': 'PASS', 'severe_memory_high': False,
                    'memory_events': dict(oom=0, oom_kill=0, max=0, high=0),
                    'metrics': dict(server_p95_mspt=10, ticks_over_50ms=20,
                                    worldgen_completion_seconds=100, client_1pct_fps=100)})
    return rows


class C2MEDecisionTests(unittest.TestCase):
    def test_safe_tie_retains_control(self):
        result = decide(series())
        self.assertEqual((result['result'], result['decision']), ('PASS', 'without_C2ME'))

    def test_worldgen_benefit_selects_four(self):
        rows = series()
        for row in rows:
            if row['variant'] == 'C2ME_4':
                row['metrics']['worldgen_completion_seconds'] = 90
        self.assertEqual(decide(rows)['decision'], 'C2ME_4')
        self.assertEqual(decide(rows), decide(rows))

    def test_credible_regressions_reject(self):
        for metric, value in [('server_p95_mspt', 11),
                              ('worldgen_completion_seconds', 104),
                              ('client_1pct_fps', 97)]:
            rows = series()
            for row in rows:
                if row['variant'] == 'C2ME_4':
                    row['metrics'][metric] = value
            with self.subTest(metric=metric):
                result = decide(rows)
                self.assertEqual(result['result'], 'FAIL')
                self.assertEqual(result['rule'], 'credible_regression')

    def test_invalid_attempt_cannot_hide_correctness_failure(self):
        rows = series()
        rows[1].update(valid=False, correctness='FAIL')
        self.assertEqual(decide(rows)['result'], 'FAIL')

    def test_resource_disqualification(self):
        for key in ('oom', 'oom_kill', 'max'):
            rows = series()
            rows[1]['memory_events'][key] = 1
            self.assertEqual(decide(rows)['result'], 'FAIL')
        rows = series()
        rows[1]['severe_memory_high'] = True
        self.assertEqual(decide(rows)['result'], 'FAIL')

    def test_unsafe_control_is_inconclusive(self):
        rows = series()
        rows[0]['correctness'] = 'FAIL'
        self.assertEqual(decide(rows)['rule'], 'unsafe_control')

    def test_incomplete_non_interleaved_or_duplicate_evidence(self):
        rows = series()
        for variant in [rows[:-1], sorted(rows, key=lambda r: (r['workload'], r['variant']))]:
            self.assertEqual(decide(variant)['result'], 'INCONCLUSIVE')
        rows[1].update(valid=False, invalid_reason='environment_noise')
        self.assertEqual(decide(rows)['rule'], 'insufficient_valid_runs')
        rows = series()
        rows[1]['clone_uuid'] = rows[0]['clone_uuid']
        self.assertEqual(decide(rows)['result'], 'INCONCLUSIVE')

    def test_missing_boolean_nonfinite_metrics_and_resource_evidence(self):
        for value in (None, True, float('nan'), float('inf'), -1, 0):
            rows = series()
            rows[1]['metrics']['server_p95_mspt'] = value
            self.assertEqual(decide(rows)['rule'], 'invalid_metric')
        rows = series()
        del rows[1]['memory_events']['max']
        self.assertEqual(decide(rows)['rule'], 'missing_resource_evidence')
        rows[1]['memory_events']['max'] = 'bad'
        self.assertEqual(decide(rows)['rule'], 'invalid_resource_evidence')

    def test_uncertain_noninferiority_cannot_select_candidate(self):
        rows = series()
        for index, row in enumerate(rows):
            if row['variant'] == 'C2ME_4':
                row['metrics']['server_p95_mspt'] = 10 if index % 3 else 15
        self.assertEqual(decide(rows)['result'], 'INCONCLUSIVE')

    def test_fallback_only_for_beneficial_safe_server_with_contention_regression(self):
        rows = series()
        for row in rows:
            if row['variant'] == 'C2ME_4':
                row['metrics']['worldgen_completion_seconds'] = 90
                row['metrics']['client_1pct_fps'] = 97
        self.assertTrue(decide(rows)['fallback_3_authorized'])
        for row in rows:
            if row['variant'] == 'C2ME_4':
                row['metrics']['worldgen_completion_seconds'] = 104
        self.assertFalse(decide(rows)['fallback_3_authorized'])

    def test_malformed_outcomes_cannot_hide_an_extra_attempt(self):
        rows = series()
        rows[1].update(valid=False)
        self.assertEqual(decide(rows)['rule'], 'malformed_run_outcome')


if __name__ == '__main__':
    unittest.main()
