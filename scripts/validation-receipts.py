"""Local exact-source receipt format and admission checks."""

import hashlib
import json
from pathlib import Path
import subprocess

EXTRA = [
    "benchmark-appliance-test",
    "immutable-etc-userborn",
    "aarch64-binfmt",
    "kexec-diagnostic-test",
    "distributed-builds",
    "stock-contamination-negative",
]


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def metadata():
    return Path(
        git("rev-parse", "--path-format=absolute", "--git-path", "local-validation")
    )


def clean():
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("exact qualification requires a clean committed tree")


def identity(commit):
    commit = git("rev-parse", "--verify", commit + "^{commit}")
    lock = subprocess.check_output(["git", "show", commit + ":flake.lock"])
    return dict(
        schema_version=1,
        repository=git("rev-list", "--max-parents=0", commit),
        commit=commit,
        tree=git("rev-parse", commit + "^{tree}"),
        clean_tree=True,
        flake_lock_sha256=hashlib.sha256(lock).hexdigest(),
    )


def receipt_path(mode, commit):
    return metadata() / "receipts" / commit / (mode + ".json")


def require(mode, commit, selector):
    if mode not in {"affected", "full", "all"}:
        raise ValueError("invalid receipt mode")
    clean()
    expected = identity(commit)
    data = json.loads(receipt_path(mode, expected["commit"]).read_text())
    if not isinstance(data, dict):
        raise ValueError("malformed receipt")
    if any(data.get(k) != v for k, v in expected.items()):
        raise ValueError("receipt source identity mismatch")
    if data.get("mode") != mode or data.get("result") != "PASS":
        raise ValueError("receipt is not a PASS for the required mode")
    for key in ("nix_version", "nixos_version", "hostname", "started", "finished"):
        if not isinstance(data.get(key), str) or not data[key]:
            raise ValueError("missing receipt provenance: " + key)
    if data["finished"] < data["started"]:
        raise ValueError("invalid receipt timestamps")
    if mode == "affected":
        base = git("rev-parse", "--verify", data["base"] + "^{commit}")
        paths = (
            subprocess.check_output(
                [
                    "git",
                    "diff",
                    "--no-renames",
                    "--name-only",
                    "-z",
                    base,
                    expected["commit"],
                ]
            )
            .decode()
            .split("\0")
        )
        selected = selector.select(paths, "affected")
    else:
        selected = selector.select([], "full")
    if any(data.get(k) != selected[k] for k in ("targets", "desktop")):
        raise ValueError("receipt selection mismatch")
    stages = ["fast"] + selected["targets"]
    if selected["desktop"]:
        stages += ["desktop"]
    if mode == "all":
        stages += EXTRA
    results = data.get("stages")
    if (
        not isinstance(results, list)
        or any(not isinstance(r, dict) for r in results)
        or [r.get("name") for r in results] != stages
        or any(r.get("result") != "PASS" for r in results)
    ):
        raise ValueError("receipt has incomplete or failed stages")
    return data
