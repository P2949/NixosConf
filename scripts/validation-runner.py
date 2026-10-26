#!/usr/bin/env python3
"""Canonical local validation and exact-commit admission."""

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
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
                    ".#" + target,
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
                for line in process.stdout:
                    sys.stdout.write(line)
                    log.write(line)
                if process.wait():
                    raise ValueError("stage failed: " + name)
            data["stages"].append(dict(name=name, result="PASS"))
    receipts.clean()
    if receipts.identity("HEAD") != source:
        raise ValueError("source changed during validation")
    data.update(finished=now(), result="PASS")
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(temporary, destination)
    receipts.require(mode, source["commit"], selector)
    print("PASS receipt: " + str(destination))


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
    args = parser.parse_args()
    os.chdir(receipts.git("rev-parse", "--show-toplevel"))
    if args.mode == "require-receipt":
        receipts.require(args.required, args.commit, selector)
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
