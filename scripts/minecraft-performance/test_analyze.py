import copy
import unittest

from analyze import decide, frame_summary, percentile


def fixture(zgc_factor=1):
    rows = []
    for variant in ("G1", "ZGC"):
        for repeat in range(5):
            rows.append({"variant": variant, "workload": "contention", "valid": True,
                         "correctness": "PASS", "metrics": {
                             "server_p95_mspt": 10 * (zgc_factor if variant == "ZGC" else 1),
                             "server_p99_mspt": 20, "ticks_over_50ms": 10,
                             "client_1pct_fps": 100, "client_p99_ms": 10,
                             "worldgen_throughput": 100}})
    return rows


class AnalysisTests(unittest.TestCase):
    def decision(self, rows):
        return decide(rows, ("contention",))

    def test_zgc_win(self):
        result = self.decision(fixture(.8))
        self.assertEqual(result["decision"], "ZGC")
        self.assertEqual(result["rule"], "server_latency_win")

    def test_g1_win(self):
        self.assertEqual(self.decision(fixture(1.2))["decision"], "G1")

    def test_tie(self):
        self.assertEqual(self.decision(fixture())["rule"], "baseline_tie")

    def test_throughput_tiebreaker_is_symmetric(self):
        for winner in ('G1', 'ZGC'):
            rows = fixture()
            for row in rows:
                if row['variant'] == winner:
                    row['metrics']['worldgen_throughput'] = 120
            result = self.decision(rows)
            self.assertEqual(result['decision'], winner)
            self.assertEqual(result['rule'], 'throughput_tiebreaker')

    def test_client_regression(self):
        rows = fixture(.8)
        for row in rows:
            if row["variant"] == "ZGC":
                row["metrics"]["client_1pct_fps"] = 90
                row["metrics"]["client_p99_ms"] = 1000 / 90
        self.assertEqual(self.decision(rows)["rule"], "zgc_client_regression")

    def test_correctness_disqualifies(self):
        rows = fixture(.8)
        rows[-1]["correctness"] = "FAIL"
        self.assertEqual(self.decision(rows)["decision"], "G1")

    def test_missing_metric(self):
        rows = fixture()
        del rows[-1]["metrics"]["server_p99_mspt"]
        self.assertEqual(self.decision(rows)["result"], "INCONCLUSIVE")

    def test_incomplete_runs(self):
        self.assertEqual(self.decision(fixture()[:-1])["result"], "INCONCLUSIVE")

    def test_memory_disqualification(self):
        rows = fixture(.8)
        rows[-1]["memory_events"] = {"oom_kill": 1}
        self.assertEqual(self.decision(rows)["decision"], "G1")

    def test_invalid_metric(self):
        rows = fixture()
        rows[-1]["metrics"]["server_p95_mspt"] = float("nan")
        self.assertEqual(self.decision(rows)["result"], "INCONCLUSIVE")

    def test_conflicting_latency_wins(self):
        rows = fixture(.8)
        other = fixture(1.2)
        for row in other:
            row["workload"] = "worldgen"
        result = decide(rows + other, ("contention", "worldgen"))
        self.assertEqual(result["result"], "INCONCLUSIVE")

    def test_reproducible(self):
        rows = fixture(.95)
        self.assertEqual(self.decision(rows), self.decision(copy.deepcopy(rows)))

    def test_frame_definition(self):
        values = list(range(1, 101))
        result = frame_summary(values)
        self.assertEqual(result["client_1pct_fps"], 1000 / percentile(values, .99))


if __name__ == "__main__":
    unittest.main()
