"""Bounded production maintenance with an independent recovery timer."""

import hashlib
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import shutil

GUARD = 'minecraft-performance-safe-recovery'
LAB = 'minecraft-performance-attribution.service'
FUNCTIONAL = 'minecraft-performance-functional.service'
CLIENT = 'minecraft-performance-client.service'
SLICE = 'minecraftperformance.slice'
SLICE_TEXT = ('[Unit]\nDescription=Disposable Minecraft qualification slice\n'
              '[Slice]\nCPUWeight=50\nIOWeight=50\n')


def call(*args):
    return subprocess.check_output(args, text=True)


def cleanup_slice(unit_root=Path('/run/systemd/system')):
    path = unit_root / SLICE
    if path.exists():
        if path.is_symlink() or path.read_text() != SLICE_TEXT:
            raise RuntimeError('refuse cleanup of unrelated slice definition')
        subprocess.run(['systemctl', 'stop', SLICE], check=True)
        path.unlink()
        subprocess.run(['systemctl', 'daemon-reload'], check=True)


def _restore_frozen_text(path, root, content):
    """Atomically restore one authenticated disposable client text input."""
    path = Path(path)
    root = Path(root)

    if not isinstance(content, str):
        raise RuntimeError('frozen client restoration content must be text')

    if (
        not root.is_absolute()
        or root.is_symlink()
        or not root.is_dir()
        or root.resolve() != root
    ):
        raise RuntimeError('disposable client root is unsafe during recovery')

    if (
        not path.is_absolute()
        or not path.is_relative_to(root)
        or path.is_symlink()
        or not path.is_file()
        or path.resolve() != path
    ):
        raise RuntimeError('disposable client restoration target is unsafe')

    info = path.stat()
    temporary = path.with_name(
        path.name + '.qualification-restore-tmp'
    )

    if os.path.lexists(temporary):
        raise RuntimeError(
            'stale disposable client restoration temporary exists'
        )

    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | os.O_CLOEXEC
        | getattr(os, 'O_NOFOLLOW', 0)
    )

    descriptor = os.open(
        temporary,
        flags,
        info.st_mode & 0o777,
    )

    try:
        with os.fdopen(
            descriptor,
            'w',
            encoding='utf-8',
        ) as stream:
            descriptor = None
            stream.write(content)
            stream.flush()
            os.fchown(stream.fileno(), info.st_uid, info.st_gid)
            os.fchmod(stream.fileno(), info.st_mode & 0o777)
            os.fsync(stream.fileno())

        os.replace(
            temporary,
            path,
        )

        directory = os.open(
            path.parent,
            os.O_RDONLY
            | os.O_DIRECTORY
            | os.O_CLOEXEC
            | getattr(os, 'O_NOFOLLOW', 0),
        )

        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    finally:
        if descriptor is not None:
            os.close(descriptor)

        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def restore_client_inputs(
    output,
    persist_root=Path('/persist'),
):
    """Restore frozen Prism inputs after stopping any qualification client."""
    manifest_path = output / 'candidate-manifest.json'

    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text())
    identity = manifest.get('client')

    if identity is None:
        return

    persist_root = Path(persist_root)
    root = Path(identity.get('root', ''))

    if (
        root.parent != persist_root
        or not root.name.startswith('minecraft-performance-client-')
        or root.is_symlink()
        or not root.is_dir()
        or root.resolve() != root
    ):
        raise RuntimeError(
            'candidate contains unsafe disposable client root'
        )

    profiles = identity.get('profiles')

    if (
        not isinstance(profiles, dict)
        or set(profiles) != {'dh-clean', 'no-dh'}
    ):
        raise RuntimeError(
            'candidate disposable client profile set is invalid'
        )

    allowed_files = {
        'options.txt',
        'config/DistantHorizons.toml',
    }

    for name, profile in profiles.items():
        instance = root / 'instances' / name

        if (
            instance.is_symlink()
            or not instance.is_dir()
            or instance.resolve() != instance
        ):
            raise RuntimeError(
                'candidate disposable client instance is unsafe'
            )

        pack = profile.get('pack')

        if not isinstance(pack, dict):
            raise RuntimeError(
                'candidate disposable client pack identity is invalid'
            )

        pack_path = Path(pack.get('path', ''))

        if pack_path != instance / 'mmc-pack.json':
            raise RuntimeError(
                'candidate disposable client pack path is invalid'
            )

        _restore_frozen_text(
            pack_path,
            root,
            pack.get('content'),
        )

        files = profile.get('files')

        if (
            not isinstance(files, dict)
            or not set(files).issubset(allowed_files)
        ):
            raise RuntimeError(
                'candidate disposable client controlled files are invalid'
            )

        for filename, entry in files.items():
            relative = Path(filename)

            if (
                relative.is_absolute()
                or '..' in relative.parts
                or not isinstance(entry, dict)
            ):
                raise RuntimeError(
                    'candidate disposable client controlled path is invalid'
                )

            _restore_frozen_text(
                instance / 'minecraft' / relative,
                root,
                entry.get('content'),
            )


def restore(output):
    # The watchdog and controller can converge here; serialize restoration.
    with (output / 'recovery.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads((output / 'maintenance.json').read_text())
        cleanup_errors = []
        client_stopped = True
        for unit in (CLIENT, LAB, FUNCTIONAL):
            try:
                if call('systemctl', 'show', unit, '-p', 'LoadState', '--value').strip() != 'not-found':
                    subprocess.run(['systemctl', 'stop', unit], check=True)
            except Exception as error:
                cleanup_errors.append({'stage': unit, 'error': str(error)})
                if unit == CLIENT:
                    client_stopped = False

        # Never write client inputs while its process may still own them.
        client_restore_error = None
        try:
            manifest_path = output / 'candidate-manifest.json'
            actual = hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest_path.exists() else None
            if actual != state.get('manifest_sha256'):
                raise RuntimeError('CLIENT_FIXTURE_MANIFEST_MISMATCH')
            if not client_stopped:
                raise RuntimeError('CLIENT_FIXTURE_PROCESS_NOT_STOPPED')
            restore_client_inputs(output)
        except Exception as error:
            client_restore_error = error
            cleanup_errors.append({'stage': 'client_inputs', 'error': str(error)})
        try:
            cleanup_slice()
        except Exception as error:
            cleanup_errors.append({'stage': 'slice', 'error': str(error)})
        (output / 'recovery-cleanup-errors.json').write_text(json.dumps(cleanup_errors, indent=2) + '\n')
        safe = Path(state['safe_system'])
        if Path('/run/current-system').resolve() != safe:
            subprocess.run([str(safe / 'bin/switch-to-configuration'), 'test'], check=True)
        subprocess.run(['systemctl', 'start', 'minecraft-server-survival.service', 'minecraft-backup.timer'], check=True)
        for unit in ('minecraft-server-survival.service', 'minecraft-backup.timer'):
            if call('systemctl', 'is-active', unit).strip() != 'active':
                raise RuntimeError('production restoration failed')
        status = call('minecraft-backup', 'status', '--live')
        (output / 'recovery-status.json').write_text(status)
        health = json.loads(status)
        if health.get('health') != 'ok' or health.get('live_verification') != 'passed':
            raise RuntimeError('live backup health after restoration failed')
        if client_restore_error is not None:
            raise RuntimeError(
                'disposable client input restoration failed after production recovery'
            ) from client_restore_error
        if cleanup_errors:
            raise RuntimeError('disposable cleanup failed after production recovery')


def arm(output):
    # No guard name may replace a pre-existing unrelated transient unit.
    for suffix in ('.service', '.timer'):
        state = call('systemctl', 'show', GUARD + suffix, '-p', 'LoadState', '--value').strip()
        if state != 'not-found':
            raise RuntimeError('recovery guard name already occupied')
    manifest_path = output / 'candidate-manifest.json'
    state = {'safe_system': str(Path('/run/current-system').resolve()),
             'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest_path.exists() else None}
    (output / 'maintenance.json').write_text(json.dumps(state) + '\n')
    recovery = output / 'recovery.py'
    shutil.copyfile(Path(__file__).resolve(), recovery)
    recovery.chmod(0o500)
    subprocess.run(['systemd-run', '--collect', '--unit=' + GUARD, '--on-active=45m',
                    '--timer-property=AccuracySec=1s', '--property=TimeoutStartSec=300',
                    sys.executable, str(recovery), str(output)], check=True)
    (output / 'guard-armed').touch(mode=0o600)


def wait_backup():
    deadline = time.monotonic() + 300
    while call('systemctl', 'show', 'minecraft-backup.service', '-p', 'ActiveState', '--value').strip() in ('active', 'activating', 'deactivating'):
        if time.monotonic() >= deadline:
            raise RuntimeError('backup transaction did not finish within maintenance bound')
        time.sleep(1)


def enter(output):
    for unit in (CLIENT, LAB, FUNCTIONAL):
        if call('systemctl', 'show', unit, '-p', 'LoadState', '--value').strip() != 'not-found':
            raise RuntimeError('qualification unit name occupied before maintenance')
    # An active backup transaction must finish before the recovery point is made.
    wait_backup()
    subprocess.run(['systemctl', 'start', 'minecraft-backup.service'], check=True)
    status = call('minecraft-backup', 'status', '--live')
    (output / 'pre-maintenance-backup.json').write_text(status)
    health = json.loads(status)
    recovery_point = health.get('state', {}).get('last_success', {})
    if (health.get('health') != 'ok' or health.get('live_verification') != 'passed'
            or not recovery_point.get('snapshot_uuid') or not recovery_point.get('filesystem_uuid')
            or not recovery_point.get('snapshot_path', '').startswith('/.snapshots/minecraft/')):
        raise RuntimeError('verified pre-maintenance recovery point required')
    arm(output)
    subprocess.run(['systemctl', 'stop', 'minecraft-backup.timer'], check=True)
    # A timer firing at the boundary must also finish before production stops.
    wait_backup()
    subprocess.run(['systemctl', 'stop', 'minecraft-server-survival.service'], check=True)
    for unit in ('minecraft-server-survival.service', 'minecraft-backup.timer', 'minecraft-backup.service'):
        if call('systemctl', 'show', unit, '-p', 'ActiveState', '--value').strip() not in ('inactive', 'failed'):
            raise RuntimeError('production/backup still active during isolated qualification')


def refresh():
    subprocess.run(['systemctl', 'restart', GUARD + '.timer'], check=True)


def disarm():
    subprocess.run(['systemctl', 'stop', GUARD + '.timer'], check=True)
    subprocess.run(['systemctl', 'reset-failed', GUARD + '.service'], check=False, capture_output=True)


if __name__ == '__main__':
    restore(Path(sys.argv[1]))
