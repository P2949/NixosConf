"""Observe pinned DH queues in tmpfs and adjudicate bounded functional recovery."""

import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import time

from dh_idle_attribution import counters
from idle_metrics import io_delta
from qualification_manifest import canonical_bytes, qualification_id, sha256
from queue_acceptance import convergence
import maintenance


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
    snapshot = root / (qualification_id(lab.manifest) + '.json')
    if snapshot.exists():
        raise ValueError('queue snapshot path already occupied')
    snapshot.touch(mode=0o600)
    subprocess.run(['chown', 'minecraft:minecraft', str(snapshot)], check=True)
    java = Path(lab.manifest['diagnostic_java_home']) / 'bin/java'
    rows = []
    start = time.monotonic()
    previous_cpu = counters(lab.cgroup / 'cpu.stat')['usage_usec']
    previous_io = (lab.cgroup / 'io.stat').read_text()
    previous_time = start
    try:
        for index in range(1, 92):
            if guarded:
                maintenance.refresh()
            time.sleep(max(0, start + index * 10 - time.monotonic()))
            # Attach output is tmpfs; clean package-power samples never run this.
            subprocess.run([str(java), '-cp', str(agent), 'local.minecraft.performance.QueueAttach',
                str(lab.pid), str(agent), str(snapshot)], check=True, timeout=10,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            observation = json.loads(snapshot.read_text())
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
                'read_bytes_per_second': delta['rbytes'] / elapsed,
                'write_bytes_per_second': delta['wbytes'] / elapsed,
                'database_fingerprint': database_hash})
            rows.append(observation)
            result = convergence(rows)
            previous_cpu, previous_io, previous_time = current_cpu, current_io, now
            if result['result'] != 'INCONCLUSIVE' or result['reason'] != 'OBSERVATION_IN_PROGRESS':
                break
        evidence.write_text(json.dumps({'result': result, 'samples': rows}, indent=2) + '\n')
        return result
    finally:
        snapshot.unlink(missing_ok=True)
