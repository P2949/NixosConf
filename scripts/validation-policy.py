"""Reject hosted CI infrastructure and the hosted-runner protocol; historical prose is unrestricted.

The scanner is deliberately not a grep for the word "github": flake inputs legitimately name it.
It rejects hosted-CI configuration roots and the names only a hosted runner provides.
"""

import os
from pathlib import Path
import sys

FORBIDDEN_PATHS = (
    ".github/workflows",
    ".github/actions",
    ".gitlab-ci.yml",
    ".gitlab-ci.yaml",
    ".circleci",
    ".travis.yml",
    "azure-pipelines.yml",
    "Jenkinsfile",
    ".buildkite",
    ".drone.yml",
    ".woodpecker",
    "bitbucket-pipelines.yml",
)
TOKENS = (
    "GITHUB_",
    "GITHUB_ACTIONS",
    "GITHUB_WORKFLOW",
    "GITHUB_EVENT_",
    "GITHUB_OUTPUT",
    "GITHUB_ENV",
    "GITHUB_STEP_SUMMARY",
    "GITHUB_REF_NAME",
    "workflow_dispatch",
    "runs-on:",
    "github.event",
    "github.sha",
    "github.ref",
    "${{ github.",
    "${{github.",
    "${{ runner.",
    "${{runner.",
)
SCANNED_EXTENSIONS = {
    ".py",
    ".sh",
    ".bash",
    ".nix",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".cfg",
    ".mk",
    ".lock",
}
SKIPPED_DIRECTORIES = {".git", "target", ".llm-runs", "dist", "result", "node_modules"}
# Where the detector, its fixtures and recorded history may name the forbidden things.
ALLOWED_FILES = {"scripts/validation-policy.py", "tests/test_validation_runner.py"}
ALLOWED_PREFIXES = (
    "docs/history/",
    "docs/reports/",
    "docs/baselines/",
    "optimization/results/",
)
MAX_SCANNED_BYTES = 2 * 1024 * 1024


def is_generic_action_reference(text):
    for line in text.splitlines():
        line = line.strip().removeprefix("- ").lstrip()
        if line.startswith("uses:") and "@" in line:
            return True
    return False


def violations(root):
    root = Path(root)
    errors = []
    for forbidden in FORBIDDEN_PATHS:
        if (root / forbidden).exists():
            errors.append(forbidden)
    for directory, names, files in os.walk(root):
        names[:] = sorted(name for name in names if name not in SKIPPED_DIRECTORIES)
        for name in sorted(files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if (
                relative in ALLOWED_FILES
                or relative.startswith(ALLOWED_PREFIXES)
                or path.suffix not in SCANNED_EXTENSIONS
                or not path.is_file()
                or path.stat().st_size > MAX_SCANNED_BYTES
            ):
                continue
            content = path.read_text(errors="replace")
            errors.extend(
                relative + ": " + token for token in TOKENS if token in content
            )
            if path.suffix in {".yml", ".yaml"} and is_generic_action_reference(
                content
            ):
                errors.append(relative + ": uses: owner/action@ref")
    return errors


if __name__ == "__main__":
    errors = violations(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    if errors:
        sys.exit("Remote CI is prohibited:\n" + "\n".join(errors))
