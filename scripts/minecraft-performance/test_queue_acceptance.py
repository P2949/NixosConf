import copy
import unittest

from queue_acceptance import convergence


class QueueConvergenceTests(unittest.TestCase):
    def samples(self, end=300):
        return [{'schema': 1, 'complete': True, 'loaded_levels': 2,
                 'queues': {'updates': 100 if elapsed < 120 else 0, 'requests': 0},
                 'elapsed': elapsed, 'cpu_one_core_pct': 2,
                 'read_bytes_per_second': 0, 'write_bytes_per_second': 0,
                 'database_fingerprint': 'a' * 64}
                for elapsed in range(0, end + 1, 10)]

    def test_bounded_catchup_can_reach_stable_zero(self):
        self.assertEqual(convergence(self.samples())['result'], 'PASS')
        self.assertEqual(convergence(self.samples(120))['result'], 'INCONCLUSIVE')

    def test_cpu_database_io_and_backlog_cannot_be_waived(self):
        for key, value in [('cpu_one_core_pct', 11), ('write_bytes_per_second', 4096),
                           ('read_bytes_per_second', 4096), ('queues', {'updates': 1, 'requests': 0})]:
            rows = self.samples(900)
            for row in rows:
                row[key] = value
            self.assertEqual(convergence(rows)['result'], 'FAIL', key)
        rows = self.samples(900)
        rows[-1]['database_fingerprint'] = 'b' * 64
        self.assertEqual(convergence(rows)['result'], 'FAIL')
        rows = self.samples()
        rows[0]['queues']['updates'] = 10001
        self.assertEqual(convergence(rows)['reason'], 'BOUNDED_BACKLOG_EXCEEDED')

    def test_missing_unknown_and_nonfinite_observations_fail_closed(self):
        original = self.samples()
        for change in ('missing', 'incomplete', 'unknown', 'nan'):
            rows = copy.deepcopy(original)
            if change == 'missing':
                rows.pop(-2)
            elif change == 'incomplete':
                rows[-1]['complete'] = False
            elif change == 'unknown':
                rows[-1]['queues']['unexpected'] = 0
            else:
                rows[-1]['cpu_one_core_pct'] = float('nan')
            self.assertEqual(convergence(rows)['result'], 'INCONCLUSIVE', change)

    def test_one_second_io_rates_distinguish_bookkeeping_from_sustained_work(self):
        rows = self.samples()
        for index, row in enumerate(rows):
            row['io_rates_one_second'] = [{'rbytes': 0, 'wbytes': 0} for _ in range(10)]
            if index % 3 == 0:
                row['io_rates_one_second'][0]['wbytes'] = 4096
        self.assertEqual(convergence(rows)['result'], 'PASS')
        for row in rows:
            row['io_rates_one_second'][0]['wbytes'] = 4096
        self.assertNotEqual(convergence(rows)['result'], 'PASS')
        for row in rows:
            row['cpu_samples_one_second'] = [0] * 8 + [50, 50]
        self.assertNotEqual(convergence(rows)['result'], 'PASS')


if __name__ == '__main__':
    unittest.main()
