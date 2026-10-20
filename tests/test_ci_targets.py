"""Regression coverage for CI admission decisions."""

import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "ci_targets", Path(__file__).resolve().parents[1] / "scripts/ci-targets.py"
)
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class SelectionTests(unittest.TestCase):
    def test_docs_and_results_skip_expensive_builds(self):
        for path in [
            "README.md",
            "docs/impermanence.md",
            "optimization/results/run.json",
        ]:
            result = ci.select([path], "pull_request")
            self.assertFalse(result["desktop"])
            self.assertFalse(result["integration"])

    def test_storage_and_core_fan_out(self):
        for path in [
            "hosts/desktop/ephemeral-root.nix",
            "modules/storage/reset.sh",
            "modules/core/nix.nix",
            "flake.lock",
        ]:
            result = ci.select([path], "pull_request")
            self.assertTrue(ci.STORAGE <= set(result["targets"]))
            self.assertTrue(result["desktop"])

    def test_home_and_minecraft(self):
        self.assertIn(
            "workstation-smoke",
            ci.select(["home/p2949/default.nix"], "pull_request")["targets"],
        )
        self.assertIn(
            "minecraft-staging",
            ci.select(["packages/minecraft-tools/main.py"], "pull_request")["targets"],
        )

    def test_main_and_manual(self):
        self.assertTrue(ci.select([], "push")["desktop"])
        self.assertTrue(
            ci.STORAGE | ci.OPTIMIZATION
            <= set(ci.select([], "workflow_dispatch")["targets"])
        )


if __name__ == "__main__":
    unittest.main()
