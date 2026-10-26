"""Regression coverage for local validation selection decisions."""

import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "validation_targets",
    Path(__file__).resolve().parents[1] / "scripts/validation-targets.py",
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
            result = ci.select([path], "affected")
            self.assertFalse(result["desktop"])
            self.assertFalse(result["integration"])

    def test_storage_and_core_fan_out(self):
        for path in [
            "hosts/desktop/ephemeral-root.nix",
            "modules/storage/reset.sh",
            "modules/core/nix.nix",
            "flake.lock",
        ]:
            result = ci.select([path], "affected")
            self.assertTrue(ci.STORAGE <= set(result["targets"]))
            self.assertTrue(result["desktop"])

    def test_home_and_minecraft(self):
        self.assertIn(
            "workstation-smoke",
            ci.select(["home/p2949/default.nix"], "affected")["targets"],
        )
        self.assertIn(
            "minecraft-staging",
            ci.select(["packages/minecraft-tools/main.py"], "affected")["targets"],
        )

    def test_home_persistence_selects_full_storage_validation(self):
        for path in [
            "home/p2949/persistence/default.nix",
            "home/p2949/persistence/ephemeral-directories.nix",
            "home/p2949/persistence/ephemeral-files.nix",
        ]:
            with self.subTest(path=path):
                result = ci.select([path], "affected")
                self.assertTrue(ci.STORAGE <= set(result["targets"]))
                self.assertIn("workstation-smoke", result["targets"])
                self.assertTrue(result["desktop"])
                self.assertTrue(result["integration"])

    def test_subsystem_selections(self):
        result = ci.select(["optimization/default.nix"], "affected")
        self.assertEqual(set(result["targets"]), ci.OPTIMIZATION)
        self.assertFalse(result["desktop"])
        result = ci.select(["home/p2949/default.nix"], "affected")
        self.assertEqual(result["targets"], ["workstation-smoke"])
        self.assertTrue(result["desktop"])
        result = ci.select(["packages/minecraft-tools/main.py"], "affected")
        self.assertEqual(result["targets"], ["minecraft-staging"])
        self.assertTrue(result["desktop"])

    def test_full_and_plumbing(self):
        expected = (
            ci.STORAGE | ci.OPTIMIZATION | {"workstation-smoke", "minecraft-staging"}
        )
        self.assertEqual(set(ci.select([], "full")["targets"]), expected)
        self.assertTrue(ci.select([], "full")["desktop"])
        for path in [
            "scripts/validate",
            "scripts/local-ci.py",
            "tests/test_ci_targets.py",
            "scripts/validation-receipts.py",
            "scripts/setup-local-validation",
            ".githooks/pre-commit",
            ".githooks/pre-push",
            "tests/test_validation_runner.py",
            "tests/default.nix",
            "flake.nix",
        ]:
            result = ci.select([path], "affected")
            self.assertEqual(set(result["targets"]), expected, path)
            self.assertTrue(result["desktop"])

    def test_compatibility_modes(self):
        for paths in (
            [],
            ["README.md"],
            ["home/p2949/default.nix"],
            ["optimization/default.nix"],
            ["flake.lock"],
        ):
            affected = ci.select(paths, "affected")
            self.assertEqual(ci.select(paths, "changed"), affected)
            main = ci.select(paths, "main")
            self.assertEqual(main["targets"], affected["targets"])
            self.assertEqual(main["integration"], affected["integration"])
            self.assertTrue(main["desktop"])
        self.assertEqual(ci.select([], "main")["targets"], [])

    def test_gpu_helper_selects_workstation(self):
        for path in [
            "packages/gamemode-gpu-profile/helper.py",
            "packages/lact/lact-auto-reset.patch",
        ]:
            with self.subTest(path=path):
                result = ci.select([path], "affected")
                self.assertEqual(result["targets"], ["workstation-smoke"])
                self.assertTrue(result["desktop"])


if __name__ == "__main__":
    unittest.main()
