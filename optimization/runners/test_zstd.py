import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import zstd


class RunnerContract(unittest.TestCase):
    def test_parser_final_record_and_failure(self):
        self.assertEqual(
            zstd.parse_output("x, 20.0 MB/s, 40.0 MB/s\rx, 21 MB/s, 42 MB/s"),
            {"compression": 21.0, "decompression": 42.0},
        )
        for output in ("truncated output", "x, 0 MB/s, 42 MB/s"):
            with self.assertRaises(ValueError):
                zstd.parse_output(output)

    def test_pinned_stock_output_syntax(self):
        # Captured from pinned stock 1.5.7; speeds normalized, never performance truth.
        record = (Path(__file__).parent / "fixtures/zstd-1.5.7.txt").read_text()
        self.assertEqual(
            set(zstd.parse_output(record)), {"compression", "decompression"}
        )

    def experiment(self, root, fail=False):
        repo = root / "repo"
        repo.mkdir()
        (repo / "flake.lock").write_text("{}")
        packages = {}
        for name in ("stock", "candidate"):
            directory = root / name
            (directory / "bin").mkdir(parents=True)
            (directory / "bin/zstd").write_text("fixture-binary-" + name)
            packages[name] = {
                "output": str(directory),
                "derivation": "fixture.drv",
                "flakeAttribute": name,
            }
        corpus = root / "corpus"
        corpus.mkdir()
        (corpus / "silesia").write_text("fixture-input")
        spec = {
            "id": "test",
            "schemaVersion": 2,
            "stage": {"kind": "fixture"},
            "physicalTarget": {},
            "targets": [
                {"id": name, "kind": "package", "attribute": name} for name in packages
            ],
            "workloads": [
                {
                    "id": "test",
                    "executable": "bin/zstd",
                    "arguments": ["-b1", "-T1"],
                    "cpu": 2,
                    "corpusId": "silesia",
                    "minimumSeconds": 1,
                    "warmupRuns": 1,
                    "metrics": [
                        {"id": name, "direction": "higher-is-better"}
                        for name in ("compression", "decompression")
                    ],
                    "sampling": {
                        "pilotPairs": 2,
                        "minimumPairs": 2,
                        "maximumPairs": 4,
                        "targetDeltaHalfWidth": 0.02,
                        "effectThreshold": 0.01,
                        "orderSeed": 1,
                    },
                }
            ],
        }
        build = {
            "schemaVersion": 1,
            "source": {
                "dirty": False,
                "revision": "fixture-commit",
                "lockSha256": zstd.digest(repo / "flake.lock"),
            },
            "stage": spec["stage"],
            "workingStock": {
                "normal": "fixture-system",
                "persistentRoot": "fixture-persistent",
                "runtime": {},
                "lockSha256": zstd.digest(repo / "flake.lock"),
                "nixpkgsRevision": "fixture",
            },
            "selectedNixpkgsRevision": "fixture",
            "evaluatedPersistentRoot": {"output": "fixture-persistent"},
            "evaluatedSystem": {"output": "fixture-system"},
            "packages": packages,
            "workloadCorpus": {"id": "silesia", "output": str(corpus)},
        }
        spec_path = root / "spec.json"
        spec_path.write_text(json.dumps(spec))
        build["specificationSha256"] = zstd.digest(spec_path)
        build_path = root / "build-provenance.json"
        build_path.write_text(json.dumps(build))
        calls = []

        def command(argv, **kwargs):
            calls.append(argv)
            if "status" in argv:
                return ""
            if "HEAD^{tree}" in argv:
                return "fixture-tree"
            if "HEAD" in argv:
                return "fixture-commit"
            return ""

        def process(argv, **kwargs):
            if argv[0] == "systemctl":
                return SimpleNamespace(stdout="active\n")
            return SimpleNamespace(
                returncode=1 if fail else 0, stdout="x, 20 MB/s, 40 MB/s", stderr=""
            )

        with (
            patch.object(zstd, "command", command),
            patch.object(zstd.subprocess, "run", process),
            patch.object(zstd.runtime, "capture", lambda: {"fixture": "runtime"}),
            patch.object(zstd.runtime, "validate_control"),
            patch.object(zstd.runtime, "validate_interval"),
        ):
            if fail:
                with self.assertRaisesRegex(ValueError, "command failed"):
                    zstd.run(
                        spec_path,
                        build_path,
                        root / "test-20261010T000000Z-fixture",
                        repo,
                    )
            else:
                zstd.run(
                    spec_path, build_path, root / "test-20261010T000000Z-fixture", repo
                )
        return root / "test-20261010T000000Z-fixture", calls

    def test_immutable_artifacts_pilot_exclusion_and_read_only_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            output, calls = self.experiment(Path(directory))
            results = json.loads((output / "results.json").read_text())
            self.assertEqual(
                results["summaries"]["test"]["metrics"]["compression"]["pairs"], 2
            )
            self.assertEqual(
                len(results["observations"]), 10
            )  # 2 warmups + 4 pilot + 4 measurement.
            index = json.loads((output / "artifact-index.json").read_text())
            self.assertEqual(index["status"], "complete")
            self.assertEqual(
                (output / "specification.json").read_bytes(),
                (Path(directory) / "spec.json").read_bytes(),
            )
            self.assertEqual(
                (output / "build-provenance.json").read_bytes(),
                (Path(directory) / "build-provenance.json").read_bytes(),
            )
            for name in (
                "specification.json",
                "build-provenance.json",
                "runtime-before.json",
                "runtime-after.json",
                "results.json",
                "execution.json",
            ):
                self.assertEqual(index["sha256"][name], zstd.digest(output / name))
            self.assertFalse(any("sudo" in x for x in calls))
            self.assertFalse(any("systemctl" in x for x in calls))

    def test_failure_retains_raw_evidence_without_state_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            output, calls = self.experiment(Path(directory), fail=True)
            self.assertEqual(
                json.loads((output / "artifact-index.json").read_text())["status"],
                "failed",
            )
            self.assertTrue(list((output / "raw").glob("*.txt")))
            self.assertFalse((output / "results.json").exists())
            self.assertFalse(any("systemctl" in x for x in calls))


if __name__ == "__main__":
    unittest.main()
