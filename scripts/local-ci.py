#!/usr/bin/env python3
"""Local verification entry point: fast, changed, full, policy, setup.

A thin dispatcher over the canonical orchestrator (`scripts/validate`); it owns no checks of its
own. Verification is local-only: it never reads GitHub state and works with `origin` unavailable.
"""

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def command(args):
    validate = str(ROOT / "scripts/validate")
    if args.command == "fast":
        return [validate, "fast"]
    if args.command == "changed":
        return [validate, "affected"] + (["--base", args.base] if args.base else [])
    if args.command == "full":
        return [validate, "full"]
    if args.command == "policy":
        return [sys.executable, str(ROOT / "scripts/validation-policy.py"), str(ROOT)]
    return [str(ROOT / "scripts/setup-local-validation")]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["fast", "full", "policy", "setup"]:
        sub.add_parser(name)
    sub.add_parser("changed").add_argument("--base")
    return subprocess.call(command(parser.parse_args(argv)), cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
