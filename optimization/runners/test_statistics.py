import unittest

# Load our module under a distinct name from Python's statistics module.
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "paired", Path(__file__).with_name("paired_statistics.py")
)
paired = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paired)


class PairedAnalysis(unittest.TestCase):
    def test_direction_and_pairing(self):
        for a, b in zip(
            paired.deltas([(100, 110), (200, 220)], "higher-is-better"),
            paired.deltas([(100, 90), (200, 180)], "lower-is-better"),
        ):
            self.assertAlmostEqual(a, b)

    def test_balanced_reproducible_order(self):
        order = paired.balanced_order(12, 7)
        self.assertEqual(order, paired.balanced_order(12, 7))
        self.assertEqual(sum(p[0] == "control" for p in order), 6)

    def test_confidence_not_just_mean(self):
        result = paired.summarize(
            [(100, 80), (100, 125), (100, 101), (100, 105)], "higher-is-better", 0.01, 7
        )
        self.assertGreater(result["meanPairedRelativeDelta"], 0)
        self.assertEqual(result["interpretation"], "inconclusive")

    def test_invalid_and_pilot_bounds(self):
        for value in [0, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                paired.deltas([(100, value), (100, 100)], "higher-is-better")
        self.assertEqual(
            paired.sample_count(
                [(100, 100), (100, 100)], "higher-is-better", 0.01, 6, 30
            ),
            6,
        )
        self.assertEqual(
            paired.sample_count(
                [(100, 1), (100, 200)], "higher-is-better", 0.01, 6, 30
            ),
            30,
        )


if __name__ == "__main__":
    unittest.main()
