"""Validated durable backup metadata and atomic publication."""
import json
import os
import re
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID
from .errors import BackupError, HEALTH_FAILURE_STAGES, HEALTH_FAILURE_MESSAGE


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")



def checked_object(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise BackupError("invalid persistent metadata fields", reason="metadata-invalid")



def checked_uuid(value):
    if not isinstance(value, str):
        raise BackupError("invalid persistent UUID", reason="metadata-invalid")
    try:
        if str(UUID(value)) != value or UUID(value).int == 0:
            raise ValueError()
    except ValueError as exc:
        raise BackupError("invalid persistent UUID", reason="metadata-invalid") from exc
    return value



def checked_time(value):
    if not isinstance(value, str):
        raise BackupError("invalid persistent UTC timestamp", reason="metadata-invalid")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
            raise ValueError()
    except ValueError as exc:
        raise BackupError("invalid persistent UTC timestamp", reason="metadata-invalid") from exc
    return value



def checked_snapshot_path(value, snapshot_root):
    if not isinstance(value, str):
        raise BackupError("invalid snapshot path", reason="metadata-invalid")
    path = Path(value)
    if (not path.is_absolute() or str(path) != value
            or path.parent != snapshot_root
            or re.fullmatch(r"survival-[0-9]{8}T[0-9]{6}(?:[0-9]{6})?Z", path.name) is None):
        raise BackupError("snapshot must be a named direct child of snapshot root", reason="metadata-invalid")
    try:
        datetime.strptime(path.name, "survival-%Y%m%dT%H%M%S%fZ"
                          if len(path.name) == 31 else "survival-%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise BackupError("invalid snapshot name timestamp", reason="metadata-invalid") from exc
    return path



def validate_record(record, snapshot_root):
    checked_object(record, ("name", "path", "created_at", "filesystem_uuid", "subvolume_uuid"))
    path = checked_snapshot_path(record["path"], snapshot_root)
    if record["name"] != path.name:
        raise BackupError("snapshot name does not match path", reason="metadata-invalid")
    checked_time(record["created_at"])
    checked_uuid(record["filesystem_uuid"])
    checked_uuid(record["subvolume_uuid"])



def validate_metadata(state, manifest, snapshot_root):
    checked_object(state, ("schema_version", "pending_snapshot", "pending_deletion", "last_attempt", "last_success", "last_retention"))
    checked_object(manifest, ("schema_version", "snapshots"))
    for value in (state, manifest):
        if type(value["schema_version"]) is not int or value["schema_version"] != 2:
            raise BackupError("unsupported persistent metadata schema", reason="metadata-invalid")
    if not isinstance(manifest["snapshots"], list):
        raise BackupError("managed snapshots must be a list", reason="metadata-invalid")
    paths, identities = set(), set()
    for record in manifest["snapshots"]:
        validate_record(record, snapshot_root)
        if record["path"] in paths or record["subvolume_uuid"] in identities:
            raise BackupError("duplicate managed snapshot identity", reason="metadata-invalid")
        paths.add(record["path"])
        identities.add(record["subvolume_uuid"])
    deletion = state["pending_deletion"]
    if deletion is not None:
        validate_record(deletion, snapshot_root)
        existing = next((r for r in manifest["snapshots"] if r["path"] == deletion["path"]), None)
        if existing is not None and existing != deletion:
            raise BackupError("deletion intent disagrees with manifest", reason="metadata-invalid")
        if state["last_success"] is not None and state["last_success"]["snapshot_path"] == deletion["path"]:
            raise BackupError("deletion intent targets last successful snapshot", reason="metadata-invalid")
        if state["pending_snapshot"] is not None and state["pending_snapshot"]["path"] == deletion["path"]:
            raise BackupError("deletion intent targets pending snapshot", reason="metadata-invalid")
    pending = state["pending_snapshot"]
    if pending is not None:
        checked_object(pending, ("path", "planned_at", "source_filesystem_uuid"))
        checked_snapshot_path(pending["path"], snapshot_root)
        checked_time(pending["planned_at"])
        checked_uuid(pending["source_filesystem_uuid"])
    success = state["last_success"]
    if success is not None:
        checked_object(success, ("created_at", "snapshot_path", "snapshot_uuid", "filesystem_uuid"))
        checked_time(success["created_at"])
        checked_snapshot_path(success["snapshot_path"], snapshot_root)
        checked_uuid(success["snapshot_uuid"])
        checked_uuid(success["filesystem_uuid"])
    attempt = state["last_attempt"]
    if attempt is not None:
        if not isinstance(attempt, dict) or attempt.get("result") not in ("success", "failed", "recovered", "aborted"):
            raise BackupError("invalid last attempt", reason="metadata-invalid")
        fields = ("started_at", "finished_at", "result")
        if attempt["result"] == "failed":
            fields += ("stage", "error_type", "message")
        checked_object(attempt, fields)
        checked_time(attempt["started_at"])
        checked_time(attempt["finished_at"])
        for field in fields:
            if not isinstance(attempt[field], str):
                raise BackupError("invalid attempt field", reason="metadata-invalid")
        if attempt["result"] == "failed" and (
                attempt["stage"] not in HEALTH_FAILURE_STAGES
                or attempt["error_type"] != "BackupError"
                or attempt["message"] != HEALTH_FAILURE_MESSAGE):
            raise BackupError("unrecognized persistent failure diagnostics", reason="metadata-invalid")
    retention = state["last_retention"]
    if retention is not None:
        checked_object(retention, ("completed_at", "result", "deleted"))
        checked_time(retention["completed_at"])
        if retention["result"] not in ("success", "failed") or not isinstance(retention["deleted"], list):
            raise BackupError("invalid retention health", reason="metadata-invalid")
        for name in retention["deleted"]:
            if not isinstance(name, str):
                raise BackupError("invalid retention name", reason="metadata-invalid")
            checked_snapshot_path(str(snapshot_root / name), snapshot_root)



def secure_state_directory(directory, create=False):
    if not os.path.lexists(directory):
        if not create:
            return False
        directory.mkdir(mode=0o700, parents=False)
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
        raise BackupError("state directory must be an owned real directory", reason="metadata-invalid")
    if stat.S_IMODE(info.st_mode) != 0o700:
        raise BackupError("state directory must have mode 0700", reason="metadata-invalid")
    return True



def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BackupError("duplicate persistent JSON key", reason="metadata-invalid")
        result[key] = value
    return result



def load_json(path, default):
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return default
    except OSError as exc:
        raise BackupError("cannot open persistent metadata", reason="metadata-invalid") from exc
    with os.fdopen(descriptor, "r") as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise BackupError("metadata must be an owned mode 0600 regular file", reason="metadata-invalid")
        try:
            return json.load(stream, object_pairs_hook=reject_duplicate_keys)
        except (ValueError, UnicodeError) as exc:
            raise BackupError("malformed persistent JSON", reason="metadata-invalid") from exc



def atomic_json(path, value):
    if not secure_state_directory(path.parent):
        raise BackupError("state directory is absent", reason="metadata-invalid")
    if os.path.lexists(path):
        load_json(path, None)
    descriptor, temporary = tempfile.mkstemp(prefix=".minecraft-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.lexists(temporary):
            os.unlink(temporary)



def load_metadata(directory=None, snapshot_root=None, create=False):
    if directory is None or snapshot_root is None:
        raise BackupError("explicit deployment policy values are required")
    exists = secure_state_directory(directory, create=create)
    state = {"schema_version": 2, "pending_snapshot": None, "pending_deletion": None, "last_attempt": None,
             "last_success": None, "last_retention": None}
    manifest = {"schema_version": 2, "snapshots": []}
    if exists:
        if (os.path.lexists(directory / "managed-snapshots.json")
                and not os.path.lexists(directory / "state.json")):
            raise BackupError("state file is missing beside an established manifest", reason="metadata-invalid")
        state = load_json(directory / "state.json", state)
        manifest = load_json(directory / "managed-snapshots.json", manifest)
    validate_metadata(state, manifest, snapshot_root)
    if state["last_success"] is not None and not os.path.lexists(directory / "managed-snapshots.json"):
        raise BackupError("managed manifest is missing after a successful snapshot", reason="metadata-invalid")
    return state, manifest

