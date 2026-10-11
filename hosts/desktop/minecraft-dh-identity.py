"""Retain DH's generated server identity while replacing declarative settings."""

import argparse
import os
import re
import tomllib
from pathlib import Path


def validate(value):
    if type(value) is not int or not -(2**31) <= value < 2**31:
        raise ValueError("DH server identity must be a signed 32-bit integer")
    return value


def capture(config, identity):
    if not config.exists():
        return
    value = tomllib.loads(config.read_text()).get("server", {}).get("serverId")
    if value is None:
        return
    value = validate(value)
    if identity.exists() and validate(int(identity.read_text())) != value:
        raise ValueError("DH server identity changed unexpectedly")
    temporary = identity.with_suffix(".tmp")
    temporary.write_text(str(value) + "\n")
    temporary.chmod(0o600)
    os.replace(temporary, identity)


def apply(config, identity):
    if not identity.exists():
        return  # First startup lets the pinned DH build generate its identity.
    value = validate(int(identity.read_text()))
    text = config.read_text()
    if "serverId" in tomllib.loads(text).get("server", {}):
        raise ValueError("DH identity must not be pinned in the policy template")
    text, count = re.subn(r"(?m)^\[server\]$", f"[server]\nserverId = {value}", text)
    if count != 1:
        raise ValueError("DH policy requires exactly one server table")
    config.write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("capture", "apply"))
    parser.add_argument("--config", type=Path, default=Path("config/DistantHorizons.toml"))
    parser.add_argument("--identity", type=Path, default=Path("config/distant-horizons-server-id"))
    args = parser.parse_args()
    try:
        {"capture": capture, "apply": apply}[args.action](args.config, args.identity)
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        raise SystemExit("DH identity preservation failed; retaining state for diagnosis") from None


if __name__ == "__main__":
    main()
