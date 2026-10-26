#!/usr/bin/env python3
"""Canonical local validation and exact-commit admission."""

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
import re
from pathlib import Path
import socket
import subprocess
import sys

sys.dont_write_bytecode = True


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).with_name(name + ".py")
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


receipts = module("validation-receipts")
selector = module("validation-targets")


def now():
    return datetime.now(timezone.utc).isoformat()


def stage_result(name, status, output):
    if name == "stock-contamination-negative":
        if (
            status not in {1, 100}
            or "contains the following disallowed paths:" not in output
            or not re.search(
                r"/nix/store/[a-z0-9]{32}-nixos-opt-pgo-fixture(?:\s|$)", output
            )
        ):
            raise ValueError(
                "negative fixture did not prove forbidden-dependency rejection"
            )
        return dict(
            name=name,
            result="PASS",
            expected_failure=True,
            exit_code=status,
            diagnostic="forbidden-dependency",
        )
    if status:
        raise ValueError("stage failed: " + name)
    return dict(name=name, result="PASS")


def run(mode, base=None, head="HEAD"):
    fast = [
        "nix",
        "flake",
        "check",
        "--no-write-lock-file",
        "--print-build-logs",
        "--builders",
        "",
        "--max-jobs",
        "2",
        "--cores",
        "2",
    ]
    if mode == "fast":
        subprocess.run(fast, check=True)
        return
    receipts.clean()
    source = receipts.identity(head)
    if source["commit"] != receipts.git("rev-parse", "HEAD"):
        raise ValueError("--head must be the checked-out commit")
    if mode == "affected":
        base = (
            receipts.git("rev-parse", "--verify", base + "^{commit}")
            if base
            else receipts.git("merge-base", head, "main")
        )
        paths = subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-only", "-z", base, source["commit"]]
        )
        selected = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    str(Path(__file__).with_name("validation-targets.py")),
                    "affected",
                ],
                input=paths,
            )
        )
    else:
        selected = selector.select([], "full")
    destination = receipts.receipt_path(mode, source["commit"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.unlink(missing_ok=True)
    logdir = receipts.metadata() / "logs" / source["commit"]
    logdir.mkdir(parents=True, exist_ok=True)
    started = now()
    data = dict(
        source,
        mode=mode,
        base=base,
        **selected,
        started=started,
        nix_version=subprocess.check_output(["nix", "--version"], text=True).strip(),
        nixos_version=subprocess.check_output(["nixos-version"], text=True).strip(),
        hostname=socket.gethostname(),
        stages=[],
    )
    # Pin Nix to committed Git content, independently of concurrent checkout edits.
    fast.insert(3, source["source_ref"])
    commands = [("fast", fast)]
    targets = selected["targets"] + (
        ["nixosConfigurations.desktop.config.system.build.toplevel"]
        if selected["desktop"]
        else []
    )
    if mode == "all":
        targets += receipts.EXTRA
    for target in targets:
        name = "desktop" if target.startswith("nixosConfigurations.") else target
        commands.append(
            (
                name,
                [
                    "nix",
                    "build",
                    source["source_ref"] + "#" + target,
                    "--no-link",
                    "--no-write-lock-file",
                    "--print-build-logs",
                    "--builders",
                    "",
                    "--max-jobs",
                    "1",
                    "--cores",
                    "2",
                ],
            )
        )
    with (logdir / (mode + "-" + started.replace(":", "-") + ".log")).open("w") as log:
        for name, command in commands:
            print("Validating " + name, flush=True)
            log.write(json.dumps(command) + "\n")
            log.flush()
            with subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            ) as process:
                output = []
                for line in process.stdout:
                    sys.stdout.write(line)
                    log.write(line)
                    if name == "stock-contamination-negative":
                        output.append(line)
                status = process.wait()
            data["stages"].append(stage_result(name, status, "".join(output)))
    receipts.clean()
    if receipts.identity("HEAD") != source:
        raise ValueError("source changed during validation")
    data.update(finished=now(), result="PASS")
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(temporary, destination)
    receipts.require(mode, source["commit"], selector)
    print("PASS receipt: " + str(destination))


def check_validator_revision(expected):
    embedded = os.environ.get("NIXOSCONF_VALIDATOR_REV", "")
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", embedded):
        raise ValueError("validator requires an embedded canonical Git commit SHA")
    if receipts.git("rev-parse", "--verify", embedded + "^{commit}") != embedded:
        raise ValueError("validator revision is not canonical")
    if embedded != receipts.git("rev-parse", "--verify", expected + "^{commit}"):
        raise ValueError("validator revision differs from the operation's commit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for mode in ("fast", "affected", "full", "all"):
        child = sub.add_parser(mode)
        if mode == "affected":
            child.add_argument("--base")
            child.add_argument("--head", default="HEAD")
    child = sub.add_parser("require-receipt")
    child.add_argument("required", choices=["affected", "full", "all"])
    child.add_argument("commit")
    child.add_argument("--base")
    args = parser.parse_args()
    os.chdir(receipts.git("rev-parse", "--show-toplevel"))
    check_validator_revision(args.commit if args.mode == "require-receipt" else "HEAD")
    if args.mode == "require-receipt":
        receipts.require(args.required, args.commit, selector, args.base)
    else:
        run(args.mode, getattr(args, "base", None), getattr(args, "head", "HEAD"))


if __name__ == "__main__":
    try:
        main()
    except (
        ValueError,
        KeyError,
        TypeError,
        OSError,
        subprocess.CalledProcessError,
    ) as error:
        sys.exit(str(error))
