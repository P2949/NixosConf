"""Retain terminal Java and cgroup evidence before a transient unit disappears."""

import json
import os
from pathlib import Path


def capture(process, group, invocation):
    events = dict(line.split() for line in (group / 'memory.events').read_text().splitlines())
    return {'schema': 1, 'invocation_id': invocation, 'java_pid': process.pid,
            'returncode': process.returncode,
            'memory_events': {k: int(v) for k, v in events.items()},
            'memory_peak_bytes': int((group / 'memory.peak').read_text())}


def write_receipt(path, process):
    groups = [line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines()
              if line.startswith('0::/')]
    if len(groups) != 1:
        raise RuntimeError('unique unified cgroup required for terminal receipt')
    receipt = capture(process, Path('/sys/fs/cgroup') / groups[0].lstrip('/'), os.environ['INVOCATION_ID'])
    with path.open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def verify(receipt, invocation, pid):
    if (receipt.get('schema') != 1 or not invocation or receipt.get('invocation_id') != invocation
            or receipt.get('java_pid') != pid or receipt.get('returncode') != 0):
        raise RuntimeError('terminal Java identity or successful exit not proven')
    events = receipt.get('memory_events', {})
    if any(type(events.get(k)) is not int or events[k] < 0 for k in ('oom', 'oom_kill', 'max', 'high')):
        raise RuntimeError('terminal memory counters not proven')
    if any(events[k] for k in ('oom', 'oom_kill', 'max')):
        raise RuntimeError('terminal memory resource disqualification')
    if type(receipt.get('memory_peak_bytes')) is not int or receipt['memory_peak_bytes'] <= 0:
        raise RuntimeError('terminal memory peak not proven')
    return receipt
