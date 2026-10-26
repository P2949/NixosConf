"""Exercise admission with real temporary Git repositories and simulated Nix stages."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "scripts", self.root / "scripts")
        shutil.copytree(ROOT / ".githooks", self.root / ".githooks")
        (self.root / "flake.lock").write_text("{}")
        self.env = dict(
            os.environ,
            PYTHONDONTWRITEBYTECODE="1",
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Test",
            GIT_AUTHOR_EMAIL="test@example.invalid",
            GIT_COMMITTER_NAME="Test",
            GIT_COMMITTER_EMAIL="test@example.invalid",
        )
        self.cmd("git", "init", "-b", "main")
        self.cmd("git", "add", ".")
        self.cmd("git", "commit", "-m", "initial")
        self.sha = self.cmd("git", "rev-parse", "HEAD").stdout.strip()
        self.bin = self.root / ".git" / "test-bin"
        self.bin.mkdir()
        for name in ("nix", "nixos-version"):
            script = self.bin / name
            script.write_text(
                '#!/bin/sh\nif [ "$1" = "shell" ]; then\n shift\n while [ "$1" != "--command" ]; do shift; done\n shift\n exec "$@"\nfi\nif [ "$1" = "--version" ] || [ "$#" = 0 ]; then echo test-version; exit; fi\nif [ "${2##*#}" = "stock-contamination-negative" ]; then\n case "${NEGATIVE_BEHAVIOR:-expected}" in\n expected) echo "System closure /nix/store/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-nixos-system-fixture contains the following disallowed paths:"; echo "/nix/store/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-nixos-opt-pgo-fixture"; exit "${NEGATIVE_STATUS:-1}" ;;\n unrelated) echo "unrelated build failure"; exit 1 ;;\n pass) exit 0 ;;\n esac\nfi\n[ "${FAIL_STAGE:-}" != "yes" ]\n'
            )
            script.chmod(0o755)
        self.env["PATH"] = str(self.bin) + os.pathsep + os.environ["PATH"]

    def cmd(self, *args, ok=True, input=None):
        result = subprocess.run(
            args,
            cwd=self.root,
            env=self.env,
            text=True,
            input=input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def validate(self, *args, **kw):
        return self.cmd(sys.executable, "scripts/validation-runner.py", *args, **kw)

    def receipt(self, mode):
        return (
            self.root / ".git/local-validation/receipts" / self.sha / (mode + ".json")
        )

    def hook(self, branch, ok):
        self.cmd(
            "sh",
            ".githooks/pre-push",
            input=f"refs/heads/main {self.sha} refs/heads/{branch} {'0' * 40}\n",
            ok=ok,
        )

    def test_receipts_and_hook(self):
        self.hook("main", False)
        self.hook("feature", False)
        self.validate("affected")
        self.validate("require-receipt", "affected", self.sha)
        self.hook("feature", True)
        self.hook("main", False)
        self.validate("full")
        self.hook("main", True)
        original = self.receipt("full").read_text()
        for key, value in [
            ("commit", "0" * 40),
            ("tree", "0" * 40),
            ("mode", "affected"),
            ("result", "FAIL"),
            ("stages", []),
            ("flake_lock_sha256", "wrong"),
            ("schema_version", 1),
            ("schema_version", 2.0),
            ("schema_version", True),
            ("clean_tree", 1),
            ("desktop", 1),
            ("integration", 1),
            ("targets", "not-a-list"),
            ("source_ref", "git+file:///wrong?rev=" + self.sha),
            ("started", "not-a-timestamp"),
            ("finished", "not-a-timestamp"),
            ("started", "2026-10-26T12:00:00"),
            ("finished", "2000-01-01T00:00:00+00:00"),
        ]:
            data = json.loads(original)
            data[key] = value
            self.receipt("full").write_text(json.dumps(data))
            self.validate("require-receipt", "full", self.sha, ok=False)
        valid = json.loads(original)
        valid["started"] = "2026-10-26T12:00:00+02:00"
        valid["finished"] = "2026-10-26T11:00:00+00:00"
        self.receipt("full").write_text(json.dumps(valid))
        self.validate("require-receipt", "full", self.sha)
        self.receipt("full").write_text("{broken")
        self.validate("require-receipt", "full", self.sha, ok=False)
        self.receipt("full").write_text(original)
        (self.root / "untracked").touch()
        self.validate("full", ok=False)
        self.validate("require-receipt", "full", self.sha, ok=False)
        (self.root / "untracked").unlink()
        self.env["FAIL_STAGE"] = "yes"
        self.validate("full", ok=False)
        self.assertFalse(self.receipt("full").exists())

    def test_exhaustive_and_head_binding(self):
        self.validate("all")
        data = json.loads(self.receipt("all").read_text())
        self.assertEqual(len(data["stages"]), 21)
        (self.root / "README.md").write_text("docs")
        self.cmd("git", "add", ".")
        self.cmd("git", "commit", "-m", "docs")
        self.validate("affected", "--head", self.sha, ok=False)
        self.validate("affected", "--base", self.sha)
        newsha = self.cmd("git", "rev-parse", "HEAD").stdout.strip()
        data = json.loads(
            (
                self.root / ".git/local-validation/receipts" / newsha / "affected.json"
            ).read_text()
        )
        self.assertEqual(data["targets"], [])
        self.assertFalse(data["desktop"])

    def test_transient_edits_cannot_change_qualified_source(self):
        # This fake Nix records the source revision each command actually addresses.
        # Dirty the checkout during fast, then restore it after the desktop build.
        executable = self.bin / "nix"
        executable.write_text(
            "#!"
            + sys.executable
            + "\n"
            + "\n".join(
                [
                    "import json, subprocess, sys",
                    "from pathlib import Path",
                    "from urllib.parse import parse_qs, urlsplit",
                    "args = sys.argv[1:]",
                    "if args == ['--version']: print('test-nix-version'); sys.exit(0)",
                    "ref = args[2] if args[0] == 'flake' else args[1]",
                    "parsed = urlsplit(ref.split('#')[0])",
                    "assert parsed.scheme == 'git+file'",
                    "rev = parse_qs(parsed.query)['rev'][0]",
                    "source = subprocess.check_output(['git', 'show', rev + ':flake.lock'], text=True)",
                    "with Path('.git/stage-sources.jsonl').open('a') as log: log.write(json.dumps({'ref': ref, 'revision': rev, 'source': source, 'checkout': Path('flake.lock').read_text()}) + '\\n')",
                    "if args[0] == 'flake': Path('flake.lock').write_text('{\"transient_change\":true}')",
                    "if ref.endswith('#nixosConfigurations.desktop.config.system.build.toplevel'): Path('flake.lock').write_text('{}')",
                ]
            )
            + "\n"
        )
        self.validate("full")
        self.validate("require-receipt", "full", self.sha)
        stages = [
            json.loads(line)
            for line in (self.root / ".git/stage-sources.jsonl")
            .read_text()
            .splitlines()
        ]
        self.assertEqual(len(stages), 15)
        self.assertTrue(
            all(
                stage["revision"] == self.sha and stage["source"] == "{}"
                for stage in stages
            )
        )
        self.assertTrue(all(stage["checkout"] != "{}" for stage in stages[1:]))
        self.assertEqual((self.root / "flake.lock").read_text(), "{}")

    def test_negative_fixture_requires_specific_rejection(self):
        for behavior in ("unrelated", "pass"):
            self.env["NEGATIVE_BEHAVIOR"] = behavior
            self.validate("all", ok=False)
            self.assertFalse(self.receipt("all").exists())
        self.env["NEGATIVE_BEHAVIOR"] = "expected"
        self.env["NEGATIVE_STATUS"] = "130"
        self.validate("all", ok=False)
        self.assertFalse(self.receipt("all").exists())
        self.env["NEGATIVE_STATUS"] = "1"
        self.validate("all")
        data = json.loads(self.receipt("all").read_text())
        self.assertTrue(data["stages"][-1]["expected_failure"])
        del data["stages"][-1]["diagnostic"]
        self.receipt("all").write_text(json.dumps(data))
        self.validate("require-receipt", "all", self.sha, ok=False)

    def test_setup_idempotent(self):
        self.cmd("sh", "scripts/setup-local-validation")
        self.cmd("sh", "scripts/setup-local-validation")
        self.assertEqual(
            self.cmd("git", "config", "core.hooksPath").stdout.strip(), ".githooks"
        )


class LocalCiDispatchTests(unittest.TestCase):
    def test_every_command_maps_to_the_canonical_orchestrator(self):
        spec = importlib.util.spec_from_file_location(
            "local_ci", ROOT / "scripts/local-ci.py"
        )
        local_ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(local_ci)
        seen = []
        local_ci.subprocess.call = lambda argv, cwd=None: seen.append(argv) or 0
        for argv in (["fast"], ["changed"], ["changed", "--base", "HEAD~1"], ["full"]):
            self.assertEqual(local_ci.main(argv), 0)
        self.assertEqual(
            [[Path(a).name for a in call[:2]] + call[2:] for call in seen],
            [
                ["validate", "fast"],
                ["validate", "affected"],
                ["validate", "affected", "--base", "HEAD~1"],
                ["validate", "full"],
            ],
        )
        local_ci.main(["policy"])
        local_ci.main(["setup"])
        self.assertTrue(seen[-2][1].endswith("validation-policy.py"))
        self.assertTrue(seen[-1][0].endswith("setup-local-validation"))


class PolicyTests(unittest.TestCase):
    def test_remote_infrastructure_and_history(self):
        spec = importlib.util.spec_from_file_location(
            "policy", ROOT / "scripts/validation-policy.py"
        )
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "history.md").write_text("GITHUB_ACTIONS workflow_dispatch")
            for name in [
                "docs/history/old.yml",
                "docs/reports/old.yaml",
                "docs/baselines/old.nix",
                "optimization/results/old.yml",
            ]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("GITHUB_ACTIONS workflow_dispatch")
            cache = root / "scripts/__pycache__/old.pyc"
            cache.parent.mkdir(parents=True)
            cache.write_bytes(b"GITHUB_ACTIONS workflow_dispatch")
            self.assertEqual(policy.violations(root), [])
            for name in [
                ".github/workflows/check.yml",
                ".gitlab-ci.yml",
                ".gitlab-ci.yaml",
                ".circleci/config.yml",
                "Jenkinsfile",
                "azure-pipelines.yml",
                ".buildkite/pipeline.yml",
            ]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
                self.assertTrue(policy.violations(root), name)
                path.unlink()
            path = root / "scripts/test.sh"
            path.parent.mkdir(exist_ok=True)
            for token in policy.TOKENS:
                path.write_text(token)
                self.assertTrue(policy.violations(root), token)


if __name__ == "__main__":
    unittest.main()
