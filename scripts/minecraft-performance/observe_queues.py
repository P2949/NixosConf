"""Observe pinned DH queues in tmpfs and adjudicate bounded functional recovery."""

import hashlib
import json
import os
from pathlib import Path
import pwd
import sqlite3
import stat
import subprocess
import time
import uuid

from dh_idle_attribution import counters
from idle_metrics import io_delta, percentile
from qualification_manifest import canonical_bytes, qualification_id, sha256
from queue_acceptance import convergence
import maintenance


def observer_directory(root, qualification, evidence_stem, owner):
    if root != root.resolve() or root.is_symlink():
        raise ValueError('noncanonical observer namespace')
    directory = root / (qualification + '-' + uuid.uuid4().hex + '-' + evidence_stem)
    directory.mkdir(mode=0o700)
    directory.chmod(0o700)
    os.chown(directory, *owner)
    metadata = directory.stat()
    return directory, (metadata.st_dev, metadata.st_ino, metadata.st_uid)


def cleanup_observer(directory, root, identity):
    if directory.parent != root or directory != directory.resolve() or directory.is_symlink():
        raise ValueError('observer cleanup path mismatch')
    metadata = directory.stat()
    if (metadata.st_dev, metadata.st_ino, metadata.st_uid) != identity:
        raise ValueError('observer directory identity changed')
    files = list(directory.iterdir())
    for path in files:
        metadata = path.lstat()
        if (path.name not in ('sample.json', 'sample.json.tmp', 'stop', 'stopped')
                or not stat.S_ISREG(metadata.st_mode) or metadata.st_uid not in (0, identity[2])):
            raise ValueError('unexpected observer cleanup entry')
    for path in files:
        path.unlink()
    directory.rmdir()


def database_state(world):
    databases = {}
    backlog = {}
    for path in sorted(world.rglob('*.sqlite')):
        name = str(path.relative_to(world))
        with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5) as db:
            columns = {row[1] for row in db.execute('PRAGMA table_info(FullData)')}
            if not {'ApplyToParent', 'ApplyToChildren', 'Regenerate'} <= columns:
                raise ValueError('unknown DH database queue schema')
            counts = db.execute('SELECT SUM(COALESCE(ApplyToParent,0)), '
                'SUM(COALESCE(ApplyToChildren,0)), SUM(COALESCE(Regenerate,0)) FROM FullData').fetchone()
            for column, value in zip(('parent', 'children', 'regenerate'), counts):
                backlog[name + '_' + column] = int(value or 0)
        databases[name] = {'size': path.stat().st_size, 'sha256': sha256(path)}
        wal = path.with_name(path.name + '-wal')
        if wal.exists():
            databases[name + '-wal'] = {'size': wal.stat().st_size, 'sha256': sha256(wal)}
    if not databases:
        raise ValueError('no DH databases observed')
    return hashlib.sha256(canonical_bytes(databases)).hexdigest(), backlog


def observe(lab, agent, evidence, *, guarded=True):
    agent = Path(agent)
    evidence = Path(evidence)
    if evidence != evidence.resolve() or not evidence.is_relative_to(lab.output):
        raise ValueError('queue evidence must remain inside canonical functional output')
    root = Path('/run/minecraft-performance-queues')
    if root.exists() and (root.is_symlink() or root.stat().st_uid != 0):
        raise ValueError('unexpected tmpfs queue namespace')
    root.mkdir(mode=0o750, exist_ok=True)
    root.chmod(0o750)
    subprocess.run(['chown', 'root:minecraft', str(root)], check=True)
    user = pwd.getpwnam('minecraft')
    directory, owned_identity = observer_directory(root, qualification_id(lab.manifest),
                                                    evidence.stem, (user.pw_uid, user.pw_gid))
    snapshot = directory / 'sample.json'
    java = Path(lab.manifest['diagnostic_java_home']) / 'bin/java'
    rows = []
    try:
        subprocess.run([str(java), '-cp', str(agent), 'local.minecraft.performance.QueueAttach',
            str(lab.pid), str(agent), str(snapshot)], check=True, timeout=10,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        start = time.monotonic()
        previous_cpu = counters(lab.cgroup / 'cpu.stat')['usage_usec']
        previous_io = (lab.cgroup / 'io.stat').read_text()
        previous_time = start
        previous_sequence = json.loads(snapshot.read_text())['sequence']
        for index in range(1, 92):
            if guarded:
                maintenance.refresh()
            rates = []
            cpu_rates = []
            sample_io, sample_time = previous_io, previous_time
            sample_cpu = previous_cpu
            for second in range(1, 11):
                time.sleep(max(0, start + (index - 1) * 10 + second - time.monotonic()))
                next_io, next_time = (lab.cgroup / 'io.stat').read_text(), time.monotonic()
                next_cpu = counters(lab.cgroup / 'cpu.stat')['usage_usec']
                if next_cpu < sample_cpu:
                    raise ValueError('queue observation CPU counter reset')
                cpu_rates.append((next_cpu - sample_cpu) / (next_time - sample_time) / 10000)
                difference = io_delta(sample_io, next_io)
                rates.append({key: difference[key] / (next_time - sample_time) for key in ('rbytes', 'wbytes')})
                sample_io, sample_time, sample_cpu = next_io, next_time, next_cpu
            observation = json.loads(snapshot.read_text())
            if observation.get('sequence', -1) <= previous_sequence:
                deadline = time.monotonic() + 2
                while observation.get('sequence', -1) <= previous_sequence and time.monotonic() < deadline:
                    time.sleep(.1)
                    observation = json.loads(snapshot.read_text())
                if observation.get('sequence', -1) <= previous_sequence:
                    raise ValueError('stale queue observer snapshot')
            previous_sequence = observation['sequence']
            database_hash, database_backlog = database_state(lab.server / 'world')
            now = time.monotonic()
            current_cpu = counters(lab.cgroup / 'cpu.stat')['usage_usec']
            current_io = (lab.cgroup / 'io.stat').read_text()
            delta = io_delta(previous_io, current_io)
            elapsed = now - previous_time
            if current_cpu < previous_cpu:
                raise ValueError('queue observation CPU counter reset')
            observation.setdefault('queues', {}).update(database_backlog)
            observation.update({'elapsed': now - start,
                'cpu_one_core_pct': (current_cpu - previous_cpu) / elapsed / 10000,
                'read_bytes_per_second': percentile([rate['rbytes'] for rate in rates], .95),
                'write_bytes_per_second': percentile([rate['wbytes'] for rate in rates], .95),
                'io_interval_delta': delta,
                'io_rates_one_second': rates, 'cpu_samples_one_second': cpu_rates,
                'database_fingerprint': database_hash})
            rows.append(observation)
            result = convergence(rows)
            previous_cpu, previous_io, previous_time = current_cpu, current_io, now
            if result['result'] != 'INCONCLUSIVE' or result['reason'] != 'OBSERVATION_IN_PROGRESS':
                break
        evidence.write_text(json.dumps({'result': result, 'samples': rows}, indent=2) + '\n')
        return result
    finally:
        (directory / 'stop').touch(mode=0o600)
        if not evidence.exists():
            evidence.write_text(json.dumps({'result': {'result': 'INCONCLUSIVE',
                'reason': 'QUEUE_OBSERVATION_ABORTED'}, 'samples': rows}, indent=2) + '\n')
        deadline = time.monotonic() + 12
        while not (directory / 'stopped').exists() and time.monotonic() < deadline:
            time.sleep(.1)
        if (directory / 'stopped').exists():
            cleanup_observer(directory, root, owned_identity)
        else:
            # Never race a still-running observer. The unique invocation cannot
            # poison later attempts, and recovery stops its disposable JVM.
            evidence.with_suffix('.cleanup.json').write_text(json.dumps({
                'result': 'INCONCLUSIVE', 'reason': 'OBSERVER_STOP_NOT_ACKNOWLEDGED',
                'retained_directory': str(directory), 'identity': owned_identity}) + '\n')
