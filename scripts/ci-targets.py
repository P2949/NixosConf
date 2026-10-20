"""Select explicit CI builds from a NUL-delimited git diff on stdin."""

import json
import os
import sys

STORAGE = {
    "granular-impermanence",
    "reset-control",
    "impermanence-root-safety",
    "interrupted-recovery",
    "persistent-identity",
    "persistent-fallback",
    "blank-disk-reconstruction",
    "recovery-iso",
    "activation-safety-actions",
}
OPTIMIZATION = {"boehmgc-compiler-preparation", "nix-evaluation-gc-consumers"}


def select(paths, event):
    targets = set()
    desktop = event in {"push", "workflow_dispatch"}
    for path in paths:
        if path.endswith(".md") or path.startswith("optimization/results/"):
            continue
        broad = path in {
            "flake.nix",
            "flake.lock",
            "tests/default.nix",
        } or path.startswith(
            (
                ".github/",
                "scripts/ci-",
                "profiles/",
                "modules/workstation/",
                "modules/core/",
                "modules/compatibility/",
            )
        )
        storage = broad or path.startswith(
            (
                "modules/storage/",
                "tests/storage/",
                "images/recovery",
                "hosts/desktop/storage",
                "hosts/desktop/ephemeral-root.nix",
                "hosts/desktop/default.nix",
                "hosts/desktop/disko",
                "hosts/desktop/persistence",
            )
        )
        if storage:
            targets.update(STORAGE)
        if broad or path.startswith(
            (
                "home/",
                "hosts/",
                "modules/",
                "tests/workstation/",
                "profiles/",
                "packages/gamemode-gpu-profile/",
            )
        ):
            targets.add("workstation-smoke")
        if broad or path.startswith(("optimization/", "tests/build/")):
            targets.update(OPTIMIZATION)
        if broad or path.startswith(
            (
                "hosts/desktop/minecraft/",
                "packages/minecraft-tools/",
                "tests/packages/minecraft-tools/",
                "tests/workstation/minecraft",
            )
        ):
            targets.add("minecraft-staging")
        if broad or path.startswith(
            ("hosts/", "home/", "modules/", "profiles/", "packages/", "images/")
        ):
            desktop = True
    if event == "workflow_dispatch":
        targets.update(
            STORAGE | OPTIMIZATION | {"workstation-smoke", "minecraft-staging"}
        )
    return {
        "targets": sorted(targets),
        "integration": bool(targets),
        "desktop": desktop,
    }


if __name__ == "__main__":
    result = select(sys.stdin.buffer.read().decode().split("\0"), sys.argv[1])
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        for key, value in result.items():
            print(f"{key}={json.dumps(value)}", file=output)
