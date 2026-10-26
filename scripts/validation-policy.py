"""Reject executable hosted CI infrastructure; historical prose is unrestricted."""

from pathlib import Path
import sys

FORBIDDEN = (".github/workflows/", ".circleci/", ".buildkite/")
FILES = {".gitlab-ci.yml", ".gitlab-ci.yaml", "Jenkinsfile", "azure-pipelines.yml"}
TOKENS = (
    "GITHUB_",
    "GITHUB_OUTPUT",
    "GITHUB_ACTIONS",
    "workflow_dispatch",
    "runs-on:",
    "uses: actions/",
    "github.event",
    "github.sha",
    "github.ref",
)


def violations(root):
    errors = []
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if ".git" in path.relative_to(root).parts or not path.is_file():
            continue
        if relative in FILES or relative.startswith(FORBIDDEN):
            errors.append(relative)
        # Policy definitions and their negative fixtures necessarily name forbidden tokens.
        operational = relative.startswith(
            (
                "scripts/",
                ".githooks/",
                ".github/",
                "hosts/",
                "modules/",
                "home/",
                "profiles/",
                "packages/",
            )
        ) or path.suffix in {".nix", ".yaml", ".yml"}
        historical = relative.startswith(
            (
                "docs/history/",
                "docs/reports/",
                "docs/baselines/",
                "optimization/results/",
            )
        )
        if (
            operational
            and not historical
            and relative != "scripts/validation-policy.py"
        ):
            content = path.read_text(errors="replace")
            errors.extend(
                relative + ": " + token for token in TOKENS if token in content
            )
    return errors


if __name__ == "__main__":
    errors = violations(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    if errors:
        sys.exit("Remote CI is prohibited:\n" + "\n".join(errors))
