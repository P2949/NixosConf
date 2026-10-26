"""Exercise admission with real temporary Git repositories and simulated Nix stages."""

import importlib.util
import json
import textwrap
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
        # Nix-store sources are read-only; transient-edit fixtures must be writable.
        for path in (self.root / "scripts").rglob("*"):
            if path.is_file():
                path.chmod(path.stat().st_mode | 0o200)
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
        fake_nix = textwrap.dedent(r"""            import json
            import os
            from pathlib import Path
            import subprocess
            import sys
            from urllib.parse import parse_qs, urlsplit

            args = sys.argv[1:]
            if not args or args == ["--version"]:
                print("test-version")
                sys.exit(0)
            if args[0] == "run":
                ref = next(arg for arg in args if arg.startswith("git+file:"))
                rev = parse_qs(urlsplit(ref.split("#")[0]).query)["rev"][0]
                with Path(".git/bootstrap.jsonl").open("a") as log:
                    log.write(json.dumps({"args": args, "ref": ref, "revision": rev}) + "\n")
                snapshot = Path(".git/fake-apps") / rev
                snapshot.mkdir(parents=True, exist_ok=True)
                for name in ("validation-runner.py", "validation-receipts.py", "validation-targets.py"):
                    content = subprocess.check_output(["git", "show", rev + ":scripts/" + name])
                    (snapshot / name).write_bytes(content)
                originals = {}
                if os.environ.get("BOOTSTRAP_EDIT"):
                    for name in ("flake.lock", "scripts/validation-runner.py", "scripts/validation-receipts.py"):
                        path = Path(name)
                        originals[path] = path.read_bytes()
                        path.write_text("transient checkout content, never authoritative")
                try:
                    env = dict(os.environ, NIXOSCONF_VALIDATOR_REV=rev)
                    status = subprocess.run([sys.executable, str(snapshot / "validation-runner.py"), *args[args.index("--") + 1:]], env=env).returncode
                finally:
                    for path, content in originals.items():
                        path.write_bytes(content)
                sys.exit(status)
            if args[0] == "build" and args[1].endswith("#stock-contamination-negative"):
                behavior = os.environ.get("NEGATIVE_BEHAVIOR", "expected")
                if behavior == "expected":
                    print("System closure /nix/store/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-nixos-system-fixture contains the following disallowed paths:")
                    print("/nix/store/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb-nixos-opt-pgo-fixture")
                    sys.exit(int(os.environ.get("NEGATIVE_STATUS", "1")))
                if behavior == "unrelated":
                    print("unrelated build failure")
                    sys.exit(1)
                sys.exit(0)
            sys.exit(1 if os.environ.get("FAIL_STAGE") == "yes" else 0)
        """)
        for name in ("nix", "nixos-version"):
            script = self.bin / name
            script.write_text("#!" + sys.executable + "\n" + fake_nix)
            script.chmod(0o755)
        self.env["PATH"] = str(self.bin) + os.pathsep + os.environ["PATH"]

    def cmd(self, *args, ok=True, input=None, env=None):
        result = subprocess.run(
            args,
            cwd=self.root,
            env=self.env if env is None else env,
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
        requested = args[2] if args[0] == "require-receipt" else "HEAD"
        revision = self.cmd("git", "rev-parse", requested + "^{commit}").stdout.strip()
        env = dict(self.env, NIXOSCONF_VALIDATOR_REV=revision)
        return self.cmd(
            sys.executable, "scripts/validation-runner.py", *args, env=env, **kw
        )

    def bootstrap(self, *args, **kw):
        return self.cmd("sh", "scripts/validate", *args, **kw)

    def bootstrap_records(self):
        return [
            json.loads(line)
            for line in (self.root / ".git/bootstrap.jsonl").read_text().splitlines()
        ]

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

    def test_bootstrap_exact_refs_and_transient_edits(self):
        self.env["FAIL_STAGE"] = "yes"
        for mode in ("fast", "affected", "full", "all"):
            self.bootstrap(mode, ok=False)
            record = self.bootstrap_records()[-1]
            self.assertEqual(record["revision"], self.sha)
            self.assertEqual(
                record["ref"],
                f"git+file://{self.root}?rev={self.sha}&allRefs=1#validation",
            )
            self.assertIn("--no-write-lock-file", record["args"])
            self.assertEqual(record["args"][record["args"].index("--builders") + 1], "")
            self.assertNotIn("--inputs-from", record["args"])
            self.assertFalse(
                any("validation-runner.py" in arg for arg in record["args"])
            )
        self.env.pop("FAIL_STAGE")
        self.env["BOOTSTRAP_EDIT"] = "yes"
        self.bootstrap("fast")
        self.assertEqual(self.bootstrap_records()[-1]["revision"], self.sha)
        self.assertEqual(self.cmd("git", "status", "--porcelain").stdout, "")

    def test_bootstrap_rejects_unsupported_repository_path(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "repo with space"
            self.cmd(
                "git", "clone", "--quiet", "--shared", str(self.root), str(destination)
            )
            result = subprocess.run(
                ["sh", "scripts/validate", "fast"],
                cwd=destination,
                env=self.env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported repository path", result.stderr)
            self.assertFalse((destination / ".git/bootstrap.jsonl").exists())

    def test_non_head_hook_uses_pushed_validator(self):
        self.bootstrap("affected")
        self.bootstrap("full")
        (self.root / "README.md").write_text("newer commit")
        self.cmd("git", "add", ".")
        self.cmd("git", "commit", "-m", "newer")
        newer = self.cmd("git", "rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(newer, self.sha)
        # The existing hook sends self.sha while HEAD is the newer commit.
        for branch, mode in (("feature", "affected"), ("main", "full")):
            self.hook(branch, True)
            record = self.bootstrap_records()[-1]
            self.assertEqual(record["revision"], self.sha)
            self.assertEqual(record["args"][-3:], ["require-receipt", mode, self.sha])
        # A direct caller cannot substitute HEAD's validator for the requested SHA.
        env = dict(self.env, NIXOSCONF_VALIDATOR_REV=newer)
        self.cmd(
            sys.executable,
            "scripts/validation-runner.py",
            "require-receipt",
            "full",
            self.sha,
            env=env,
            ok=False,
        )

    def test_embedded_revision_is_mandatory_and_exact(self):
        for revision in ("", "dirty", self.sha[:12], "0" * 40):
            env = dict(self.env, NIXOSCONF_VALIDATOR_REV=revision)
            self.cmd(
                sys.executable,
                "scripts/validation-runner.py",
                "fast",
                env=env,
                ok=False,
            )
        env = dict(self.env)
        env.pop("NIXOSCONF_VALIDATOR_REV", None)
        self.cmd(
            sys.executable, "scripts/validation-runner.py", "fast", env=env, ok=False
        )

    def test_closed_schema_and_duplicate_keys(self):
        self.validate("full")
        original = self.receipt("full").read_text()
        edits = [
            lambda d: d.update(unknown=True),
            lambda d: d.pop("hostname"),
            lambda d: d.update(base=self.sha),
            lambda d: d["stages"][0].update(extra="unexpected"),
            lambda d: d["stages"][0].pop("result"),
            lambda d: d["stages"][0].update(name=1),
            lambda d: d["stages"][0].update(result=True),
        ]
        for edit in edits:
            data = json.loads(original)
            edit(data)
            self.receipt("full").write_text(json.dumps(data))
            self.validate("require-receipt", "full", self.sha, ok=False)
        for raw in (
            original[:-2] + ', "mode": "full"}',
            original.replace('"name": "fast"', '"name": "fast", "name": "fast"', 1),
        ):
            json.loads(raw)  # Legal JSON syntax with duplicate object keys.
            self.receipt("full").write_text(raw)
            result = self.validate("require-receipt", "full", self.sha, ok=False)
            self.assertIn("duplicate receipt key", result.stderr)
        self.validate("affected")
        data = json.loads(self.receipt("affected").read_text())
        data["base"] = None
        self.receipt("affected").write_text(json.dumps(data))
        self.validate("require-receipt", "affected", self.sha, ok=False)
        self.validate("all")
        original_all = self.receipt("all").read_text()
        for edit in (
            lambda d: d.update(base=self.sha),
            lambda d: d["stages"][-1].update(extra=True),
        ):
            data = json.loads(original_all)
            edit(data)
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
