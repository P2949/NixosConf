import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import nix_evaluation as runner
import test_runtime


class EvaluationAdmissionTests(unittest.TestCase):
    def test_only_expected_live_gc_mapping_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "nix"
            executable.touch()
            process = root / "123"
            process.mkdir()
            (process / "exe").symlink_to(executable)
            library = Path("/nix/store/candidate/lib/libgc.so.1.5.6")
            mapping = f"1000-2000 r-xp 00000000 00:00 1 {library}\n"
            (process / "maps").write_text(mapping)
            receipt = runner.process_binding(123, executable, library, root)
            self.assertEqual(receipt["gcMappings"], [str(library)])
            (process / "maps").write_text(
                mapping + mapping.replace("candidate", "stock")
            )
            with self.assertRaisesRegex(ValueError, "unexpected GC"):
                runner.process_binding(123, executable, library, root)
            (process / "maps").write_text(mapping.rstrip() + " (deleted)\n")
            with self.assertRaisesRegex(ValueError, "deleted"):
                runner.process_binding(123, executable, library, root)
            self.assertIsNone(
                runner.process_binding(123, root / "different", library, root)
            )

    def test_failed_child_retains_output_receipt_and_private_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix = root / "failed"
            argv = [
                sys.executable,
                "-c",
                "import json,os; print(json.dumps(dict(os.environ))); print('failure detail',file=__import__('sys').stderr); raise SystemExit(7)",
            ]
            with patch.dict(
                os.environ,
                {"NIX_CONFIG": "untrusted-parent", "PARENT_SECRET": "must-not-inherit"},
            ):
                with self.assertRaisesRegex(ValueError, "exited before"):
                    runner.execute_observation(
                        argv,
                        root / "state",
                        Path(sys.executable).resolve(),
                        Path("/missing-gc"),
                        prefix,
                    )
            child = json.loads(prefix.with_suffix(".stdout").read_text())
            self.assertNotEqual(child["NIX_CONFIG"], "untrusted-parent")
            self.assertIn("accept-flake-config = false", child["NIX_CONFIG"])
            self.assertNotIn("PARENT_SECRET", child)
            self.assertEqual(child["HOME"], str(root / "state/home"))
            self.assertIn("failure detail", prefix.with_suffix(".stderr").read_text())
            receipt = json.loads(prefix.with_suffix(".receipt.json").read_text())
            self.assertEqual(receipt["returncode"], 7)
            self.assertIn("error", receipt)
            self.assertEqual((root / "state").stat().st_mode & 0o777, 0o700)

    def test_corpus_rejects_missing_graph_node_and_changed_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            lock = {
                "nodes": {
                    "root": {},
                    "dependency": {
                        "locked": {"narHash": "sha256-expected", "rev": "revision"}
                    },
                }
            }
            (source / "flake.lock").write_text(json.dumps(lock))
            manifest = {
                "kind": "nixos-nix-evaluation-corpus",
                "schemaVersion": 1,
                "source": {
                    "path": str(source),
                    "lockSha256": runner.digest(source / "flake.lock"),
                    "narHash": "sha256-root",
                },
                "inputs": {},
            }
            corpus = root / "corpus.json"
            corpus.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "graph mismatch"):
                runner.validate_corpus(corpus, Path("/unused-nix"))
            changed = copy.deepcopy(manifest)
            changed["inputs"]["dependency"] = {
                "path": str(source),
                "narHash": "sha256-changed",
                "revision": "revision",
            }
            corpus.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                runner.validate_corpus(corpus, Path("/unused-nix"))
            changed["source"]["lockSha256"] = "incorrect"
            corpus.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "lock hash"):
                runner.validate_corpus(corpus, Path("/unused-nix"))

    def test_gc_policy_cannot_change_with_cpu_flags(self):
        base = {
            "kind": "nixos-nix-evaluation-build",
            "collectorPolicy": {
                "enableLargeConfig": True,
                "initialMarkStackSize": 1048576,
            },
            "stage": {
                "parameters": {
                    "march": "skylake",
                    "mtune": "skylake",
                    "packageAllowList": ["boehm-gc"],
                }
            },
        }
        gc = {
            "source": {"output": "pinned-source", "derivation": "pinned-derivation"},
            "version": "8.2.12",
            "configureFlags": ["--enable-large-config"],
            "makeFlags": ["CFLAGS_EXTRA=-DINITIAL_MARK_STACK_SIZE=1048576"],
            "compileFlags": "",
            "output": "/nix/store/stock",
        }
        base["libraries"] = {
            "stock": gc,
            "candidate": {
                **gc,
                "compileFlags": "-march=skylake -mtune=skylake",
                "output": "/nix/store/candidate",
            },
        }
        for field, value in [
            ("version", "other"),
            ("makeFlags", []),
            ("source", {"output": "other"}),
            ("compileFlags", "-march=native"),
        ]:
            changed = copy.deepcopy(base)
            changed["libraries"]["candidate"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                runner.validate_libraries(changed)


class EvaluationEvidenceTests(unittest.TestCase):
    @contextmanager
    def experiment(self, root):
        # Synthetic observations test evidence handling, never performance truth.
        repo = root / "repo"
        repo.mkdir()
        (repo / "flake.lock").write_text("{}")
        packages, libraries = {}, {}
        for variant in ("stock", "candidate"):
            package = root / variant
            (package / "bin").mkdir(parents=True)
            (package / "bin/nix-evaluation").write_text("fixture-wrapper-" + variant)
            packages[variant] = {
                "output": str(package),
                "derivation": "fixture.drv",
                "flakeAttribute": "nix-evaluation-" + variant,
            }
            library = root / (variant + ".so")
            library.write_text("fixture-library-" + variant)
            libraries[variant] = library
        consumer = root / "consumer"
        (consumer / "bin").mkdir(parents=True)
        (consumer / "bin/nix").write_text("fixture-consumer")
        corpus = root / "corpus.json"
        identity = {"source": {"path": str(repo)}, "inputs": {}}
        corpus.write_text(json.dumps(identity))
        runtime_root = root / "runtime-fixture"
        runtime_root.mkdir()
        contract = test_runtime.RuntimeContract()
        contract.fixture(runtime_root)
        snapshot = contract.snapshot(runtime_root)
        stage = {
            "kind": "cpu-codegen",
            "parameters": {
                "march": "skylake",
                "mtune": "skylake",
                "packageAllowList": ["boehm-gc"],
            },
        }
        spec = {
            "schemaVersion": 2,
            "id": "fixture",
            "stage": stage,
            "physicalTarget": {
                "hostname": "fixture",
                "cpuVendor": "GenuineIntel",
                "cpuFamily": "6",
                "cpuModel": "165",
            },
            "targets": [
                {"id": key, "kind": "package", "attribute": value["flakeAttribute"]}
                for key, value in packages.items()
            ],
            "workloads": [
                {
                    "id": "repository-evaluation",
                    "executable": "bin/nix-evaluation",
                    "arguments": [
                        "flake",
                        "check",
                        "@source@",
                        "--offline",
                        "--no-build",
                        "--no-write-lock-file",
                        "--no-eval-cache",
                    ],
                    "corpusId": "nix-evaluation",
                    "cpu": 2,
                    "warmupRuns": 1,
                    "minimumSeconds": 1,
                    "metrics": [
                        {"id": key, "direction": "lower-is-better"}
                        for key in ("wallTime", "cpuTime")
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
        spec_path = root / "spec.json"
        spec_path.write_text(json.dumps(spec))
        build = {
            "schemaVersion": 1,
            "kind": "nixos-nix-evaluation-build",
            "source": {
                "dirty": False,
                "revision": "f" * 40,
                "lockSha256": runner.digest(repo / "flake.lock"),
            },
            "stage": stage,
            "workingStock": {
                "normal": "/nix/store/fixture-system",
                "persistentRoot": "fixture-persistent",
                "runtime": contract.expected(),
                "lockSha256": runner.digest(repo / "flake.lock"),
                "nixpkgsRevision": "fixture",
            },
            "selectedNixpkgsRevision": "fixture",
            "evaluatedPersistentRoot": {"output": "fixture-persistent"},
            "evaluatedSystem": {"output": "/nix/store/fixture-system"},
            "packages": packages,
            "workloadCorpus": {"id": "nix-evaluation", "output": str(corpus)},
            "consumer": {"output": str(consumer), "executable": "bin/nix"},
            "specificationSha256": runner.digest(spec_path),
        }
        build_path = root / "build.json"
        build_path.write_text(json.dumps(build))
        output = root / "fixture-20261015T000000Z-fffffff"

        def command(argv, **kwargs):
            if "status" in argv:
                return ""
            return "e" * 40 if "HEAD^{tree}" in argv else "f" * 40

        def execute(argv, state, executable, library, prefix):
            state.mkdir(mode=0o700)
            candidate = "candidate" in state.name
            timing = (
                10.0
                if candidate and "-pilot-" in state.name
                else 90.0
                if candidate
                else 100.0
            )
            metrics = {"wallTime": timing, "cpuTime": timing}
            started = runner.now()
            prefix.with_suffix(".stdout").write_text("synthetic fixture output")
            prefix.with_suffix(".stderr").write_text("")
            receipt = {
                "stateDirectory": str(state),
                "environment": {
                    "PATH": os.environ["PATH"],
                    "LC_ALL": "C",
                    "TZ": "UTC",
                    "HOME": str(state / "home"),
                    "XDG_CACHE_HOME": str(state / "cache"),
                    "XDG_CONFIG_HOME": str(state / "config"),
                    "XDG_STATE_HOME": str(state / "state"),
                    "NIX_USER_CONF_FILES": "/dev/null",
                    "NIX_CONF_DIR": str(state / "config"),
                    "NIX_CONFIG": "experimental-features = nix-command flakes\naccept-flake-config = false\n",
                },
                "argv": argv,
                "returncode": 0,
                "metrics": metrics,
                "monotonicStart": 0.0,
                "monotonicEnd": timing,
                "childUsageBefore": {"user": 0.0, "system": 0.0},
                "childUsageAfter": {"user": timing, "system": 0.0},
                "startedAt": started,
                "finishedAt": runner.now(),
                "binding": {
                    "pid": 123,
                    "executable": str(executable),
                    "gcMappings": [str(library)],
                    "observedAt": started,
                },
            }
            prefix.with_suffix(".receipt.json").write_text(json.dumps(receipt))
            return metrics

        with (
            patch.object(runner, "command", command),
            patch.object(runner, "validate_libraries", return_value=libraries),
            patch.object(runner, "validate_corpus", return_value=identity),
            patch.object(runner, "execute_observation", execute),
            patch.object(
                runner.runtime, "capture", side_effect=lambda: copy.deepcopy(snapshot)
            ),
        ):
            runner.run(spec_path, build_path, output, repo)
            yield output

    def reindex(self, output, names):
        path = output / "artifact-index.json"
        index = json.loads(path.read_text())
        for name in names:
            index["sha256"][name] = runner.digest(output / name)
        path.write_text(json.dumps(index))

    def test_complete_bundle_reconstructs_and_excludes_pilot(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            self.experiment(Path(directory)) as output,
        ):
            reconstructed = runner.verify(output)
            metric = reconstructed["repository-evaluation"]["metrics"]["wallTime"]
            self.assertEqual(
                metric["candidate"]["mean"], 90.0
            )  # pilot candidate is 10.0.
            self.assertEqual(metric["pairs"], 2)
            self.assertEqual(
                len(json.loads((output / "results.json").read_text())["observations"]),
                10,
            )
            raw = next((output / "raw").glob("*.stdout"))
            raw.write_text("altered")
            with self.assertRaisesRegex(ValueError, "artifact hash"):
                runner.verify(output)

    def test_reindexed_statistics_tampering_is_rejected(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            self.experiment(Path(directory)) as output,
        ):
            path = output / "results.json"
            value = json.loads(path.read_text())
            value["summaries"]["repository-evaluation"]["metrics"]["wallTime"][
                "interpretation"
            ] = "regression"
            path.write_text(json.dumps(value))
            self.reindex(output, ["results.json"])
            with self.assertRaisesRegex(ValueError, "statistics reconstruction"):
                runner.verify(output)

    def test_reindexed_wrong_library_is_rejected(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            self.experiment(Path(directory)) as output,
        ):
            path = next((output / "raw").glob("*.receipt.json"))
            value = json.loads(path.read_text())
            value["binding"]["gcMappings"] = ["/unexpected/library"]
            path.write_text(json.dumps(value))
            self.reindex(output, [str(path.relative_to(output))])
            with self.assertRaisesRegex(ValueError, "process binding"):
                runner.verify(output)

    def test_reindexed_between_observation_policy_change_is_rejected(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            self.experiment(Path(directory)) as output,
        ):
            path = next((output / "raw").glob("*-runtime.json"))
            value = json.loads(path.read_text())
            for snapshot in (value["before"], value["after"]):
                snapshot["memory"]["numaBalancing"]["value"] = "1"
            path.write_text(json.dumps(value))
            self.reindex(output, [str(path.relative_to(output))])
            with self.assertRaisesRegex(ValueError, "memory policy"):
                runner.verify(output)

    def test_reindexed_private_configuration_change_is_rejected(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            self.experiment(Path(directory)) as output,
        ):
            path = next((output / "raw").glob("*.receipt.json"))
            value = json.loads(path.read_text())
            value["environment"]["NIX_CONF_DIR"] = "/etc/nix"
            path.write_text(json.dumps(value))
            self.reindex(output, [str(path.relative_to(output))])
            with self.assertRaisesRegex(ValueError, "environment identity"):
                runner.verify(output)


if __name__ == "__main__":
    unittest.main()
