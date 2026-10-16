"""Negative admission checks against Nix-generated comparison artifacts."""

import copy
import json
import os
from pathlib import Path
import unittest

from gc_compiler import validate_preparation
import nix_evaluation


class CompilerPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = [
            json.loads(Path(path).read_text())
            for path in json.loads(os.environ["GC_COMPILER_ARTIFACTS"])
        ]
        if not cls.artifacts:
            raise ValueError("real comparison artifacts required")
        cls.measurements = [
            json.loads(Path(path).read_text())
            for path in json.loads(
                os.environ.get("GC_COMPILER_MEASUREMENT_ARTIFACTS", "[]")
            )
        ]

    def test_generated_measurement_bindings(self):
        if not self.measurements:
            self.skipTest("measurement artifacts not supplied")
        for build in self.measurements:
            with self.subTest(comparison=build["compilerComparison"]["comparison"]):
                libraries = nix_evaluation.validate_libraries(build)
                self.assertEqual(set(libraries), {"stock", "candidate"})
                self.assertIn("gcCompiler", nix_evaluation.support_modules(build))

    def test_unbound_measurement_stage_rejected(self):
        if not self.measurements:
            self.skipTest("measurement artifacts not supplied")
        for build in self.measurements:
            altered = copy.deepcopy(build)
            altered["stage"]["parameters"]["comparison"] = "unbound"
            with self.subTest(comparison=build["compilerComparison"]["comparison"]):
                with self.assertRaisesRegex(
                    ValueError, "compiler comparison stage mismatch"
                ):
                    nix_evaluation.validate_libraries(altered)

    def test_command_substitution_rejected(self):
        if not self.measurements:
            self.skipTest("measurement artifacts not supplied")
        for build in self.measurements:
            altered = copy.deepcopy(build)
            altered["packages"]["candidate"]["output"] = altered["packages"]["stock"][
                "output"
            ]
            with self.subTest(comparison=build["compilerComparison"]["comparison"]):
                with self.assertRaisesRegex(
                    ValueError, "comparison command binding mismatch"
                ):
                    nix_evaluation.validate_libraries(altered)

    def test_real_artifacts_and_build_evidence(self):
        for artifact in self.artifacts:
            with self.subTest(comparison=artifact["comparison"]):
                result = validate_preparation(artifact)
                self.assertEqual(
                    result["acceptance"], "PREPARATION_ONLY_NOT_PERFORMANCE"
                )

    def test_unrelated_flags_rejected(self):
        for artifact in self.artifacts:
            altered = copy.deepcopy(artifact)
            altered["libraries"]["candidate"]["compileFlags"] += " -ffast-math"
            with self.subTest(comparison=artifact["comparison"]):
                with self.assertRaisesRegex(
                    ValueError, "unexpected candidate compile flags"
                ):
                    validate_preparation(altered)

    def test_missing_candidate_audit_rejected(self):
        for artifact in self.artifacts:
            altered = copy.deepcopy(artifact)
            altered["libraries"]["candidate"]["audit"] = None
            with self.subTest(comparison=artifact["comparison"]):
                with self.assertRaisesRegex(ValueError, "compiler audit required"):
                    validate_preparation(altered)

    def test_collector_policy_change_rejected(self):
        for artifact in self.artifacts:
            altered = copy.deepcopy(artifact)
            altered["libraries"]["candidate"]["makeFlags"] = []
            with self.subTest(comparison=artifact["comparison"]):
                with self.assertRaisesRegex(
                    ValueError, "package source/policy changed"
                ):
                    validate_preparation(altered)

    def test_toolchain_change_cannot_be_misattributed(self):
        for artifact in self.artifacts:
            if artifact["comparison"] == "toolchain-bridge":
                continue
            altered = copy.deepcopy(artifact)
            altered["libraries"]["candidate"]["toolchain"]["compilerVersion"] = (
                "different"
            )
            with self.subTest(comparison=artifact["comparison"]):
                with self.assertRaisesRegex(ValueError, "toolchain changed alongside"):
                    validate_preparation(altered)

    def test_preparation_cannot_claim_performance_acceptance(self):
        altered = copy.deepcopy(self.artifacts[0])
        altered["acceptance"] = "PERFORMANCE_ACCEPTED"
        with self.assertRaisesRegex(ValueError, "unexpected comparison evidence class"):
            validate_preparation(altered)


if __name__ == "__main__":
    unittest.main()
