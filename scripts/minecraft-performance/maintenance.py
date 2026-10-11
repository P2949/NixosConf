"""Bounded production maintenance with an independent recovery timer."""

import fcntl
import json
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


def cleanup_slice():
    path = Path('/run/systemd/system') / SLICE
    if path.exists():
        if path.is_symlink() or path.read_text() != SLICE_TEXT:
            raise RuntimeError('refuse cleanup of unrelated slice definition')
        subprocess.run(['systemctl', 'stop', SLICE], check=True)
        path.unlink()
        subprocess.run(['systemctl', 'daemon-reload'], check=True)


def restore(output):
    # The watchdog and controller can converge here; serialize restoration.
    with (output / 'recovery.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads((output / 'maintenance.json').read_text())
        for unit in (CLIENT, LAB, FUNCTIONAL):
            if call('systemctl', 'show', unit, '-p', 'LoadState', '--value').strip() != 'not-found':
                subprocess.run(['systemctl', 'stop', unit], check=True)
        cleanup_slice()
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


def arm(output):
    # No guard name may replace a pre-existing unrelated transient unit.
    for suffix in ('.service', '.timer'):
        state = call('systemctl', 'show', GUARD + suffix, '-p', 'LoadState', '--value').strip()
        if state != 'not-found':
            raise RuntimeError('recovery guard name already occupied')
    state = {'safe_system': str(Path('/run/current-system').resolve())}
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
