"""Local exact-source receipt format and admission checks."""

from datetime import datetime
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


def pinned_ref(commit):
    root = Path(git("rev-parse", "--show-toplevel")).as_uri()
    return f"git+{root}?rev={commit}&allRefs=1"


def identity(commit):
    commit = git("rev-parse", "--verify", commit + "^{commit}")
    lock = subprocess.check_output(["git", "show", commit + ":flake.lock"])
    return dict(
        schema_version=2,
        source_ref=pinned_ref(commit),
        repository=git("rev-list", "--max-parents=0", commit),
        commit=commit,
        tree=git("rev-parse", commit + "^{tree}"),
        clean_tree=True,
        flake_lock_sha256=hashlib.sha256(lock).hexdigest(),
    )


def receipt_path(mode, commit):
    return metadata() / "receipts" / commit / (mode + ".json")


RECEIPT_KEYS = {
    "schema_version",
    "source_ref",
    "repository",
    "commit",
    "tree",
    "clean_tree",
    "flake_lock_sha256",
    "mode",
    "base",
    "targets",
    "integration",
    "desktop",
    "started",
    "finished",
    "nix_version",
    "nixos_version",
    "hostname",
    "stages",
    "result",
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate receipt key: " + key)
        result[key] = value
    return result


def require(mode, commit, selector, expected_base=None):
    if mode not in {"affected", "full", "all"}:
        raise ValueError("invalid receipt mode")
    if mode != "affected" and expected_base is not None:
        raise ValueError("an expected base applies only to affected receipts")
    clean()
    expected = identity(commit)
    data = json.loads(
        receipt_path(mode, expected["commit"]).read_text(),
        object_pairs_hook=unique_object,
    )
    if not isinstance(data, dict) or set(data) != RECEIPT_KEYS:
        raise ValueError("malformed receipt")
    if any(
        type(data.get(k)) is not type(v) or data.get(k) != v
        for k, v in expected.items()
    ):
        raise ValueError("receipt source identity mismatch")
    if data.get("mode") != mode or data.get("result") != "PASS":
        raise ValueError("receipt is not a PASS for the required mode")
    for key in ("nix_version", "nixos_version", "hostname", "started", "finished"):
        if not isinstance(data.get(key), str) or not data[key]:
            raise ValueError("missing receipt provenance: " + key)
    timestamps = [datetime.fromisoformat(data[key]) for key in ("started", "finished")]
    if any(value.tzinfo is None or value.utcoffset() is None for value in timestamps):
        raise ValueError("receipt timestamps require time zones")
    if timestamps[1] < timestamps[0]:
        raise ValueError("invalid receipt timestamps")
    if mode == "affected":
        if not isinstance(data.get("base"), str):
            raise ValueError("missing affected base SHA")
        base = git("rev-parse", "--verify", data["base"] + "^{commit}")
        if data["base"] != base:
            raise ValueError("affected base must be an exact commit SHA")
        if expected_base is not None and (
            git("rev-parse", "--verify", expected_base + "^{commit}") != base
        ):
            raise ValueError("affected receipt base differs from the expected base")
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
        if data["base"] is not None:
            raise ValueError("full/all base must be null")
        selected = selector.select([], "full")
    if any(
        type(data.get(k)) is not type(selected[k]) or data.get(k) != selected[k]
        for k in ("targets", "integration", "desktop")
    ):
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
    for stage in results:
        keys = {"name", "result"}
        if stage["name"] == "stock-contamination-negative":
            keys |= {"expected_failure", "exit_code", "diagnostic"}
        if (
            set(stage) != keys
            or type(stage["name"]) is not str
            or type(stage["result"]) is not str
        ):
            raise ValueError("malformed receipt stage")
    if mode == "all":
        negative = results[-1]
        if (
            negative.get("expected_failure") is not True
            or type(negative.get("exit_code")) is not int
            or negative["exit_code"] not in {1, 100}
            or negative.get("diagnostic") != "forbidden-dependency"
        ):
            raise ValueError("missing negative fixture rejection evidence")
    return data
