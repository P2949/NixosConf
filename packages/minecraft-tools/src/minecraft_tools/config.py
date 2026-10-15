"""Strict non-secret deployment policy shared by Minecraft tools."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MinecraftConfig:
    source: Path
    snapshot_mount: Path
    snapshot_root: Path
    state_directory: Path
    runtime_directory: Path
    management_host: str
    management_port: int
    environment_file: Path
    keep_snapshots: int
    source_fs_root: str
    snapshot_fs_root: str

    @property
    def management_url(self) -> str:
        host = (
            f"[{self.management_host}]"
            if ":" in self.management_host
            else self.management_host
        )
        return f"ws://{host}:{self.management_port}"


def _object(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError("configuration fields do not match schema")
    return value


def _path(value):
    if not isinstance(value, str) or not value.startswith("/"):
        raise ValueError("configuration paths must be absolute")
    if (
        value == "/"
        or any(part in {"", ".", ".."} for part in value.split("/")[1:])
        or any(ord(c) < 32 for c in value)
    ):
        raise ValueError("configuration paths must be normalized non-root paths")
    return Path(value)


def _integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("configuration integer outside allowed range")
    return value


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate configuration field")
        result[key] = value
    return result


def load_config(path: Path) -> MinecraftConfig:
    policy = _object(
        json.loads(path.read_text(), object_pairs_hook=_unique),
        (
            "schemaVersion",
            "source",
            "snapshotMount",
            "snapshotRoot",
            "stateDirectory",
            "runtimeDirectory",
            "management",
            "retention",
            "btrfs",
        ),
    )
    _integer(policy["schemaVersion"], 1, 1)
    management = _object(policy["management"], ("host", "port", "environmentFile"))
    retention = _object(policy["retention"], ("snapshots",))
    btrfs = _object(policy["btrfs"], ("sourceRoot", "snapshotRoot"))
    host = management["host"]
    if not isinstance(host, str) or host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("management host must be loopback")
    result = MinecraftConfig(
        source=_path(policy["source"]),
        snapshot_mount=_path(policy["snapshotMount"]),
        snapshot_root=_path(policy["snapshotRoot"]),
        state_directory=_path(policy["stateDirectory"]),
        runtime_directory=_path(policy["runtimeDirectory"]),
        management_host=host,
        management_port=_integer(management["port"], 1, 65535),
        environment_file=_path(management["environmentFile"]),
        keep_snapshots=_integer(retention["snapshots"], 1, 10000),
        source_fs_root=str(_path(btrfs["sourceRoot"])),
        snapshot_fs_root=str(_path(btrfs["snapshotRoot"])),
    )
    if result.snapshot_root.parent != result.snapshot_mount:
        raise ValueError("snapshot root must be a direct child of snapshot mount")
    paths = (
        result.source,
        result.snapshot_mount,
        result.state_directory,
        result.runtime_directory,
    )
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            if left == right or left in right.parents or right in left.parents:
                raise ValueError("deployment directories must be disjoint")
    if result.source_fs_root == result.snapshot_fs_root:
        raise ValueError("source and snapshots require distinct subvolumes")
    return result
