"""Executable bounded convergence policy for functional DH queue workloads."""

import math
import statistics

from idle_metrics import percentile


def convergence(samples, *, timeout=900, quiet_seconds=180, max_backlog=10000):
    if not samples:
        return {'result': 'INCONCLUSIVE', 'reason': 'NO_SAMPLES'}
    queue_keys = None
    for row in samples:
        if not isinstance(row, dict):
            return {'result': 'INCONCLUSIVE', 'reason': 'INVALID_OBSERVATION'}
        if row.get('schema') != 1 or row.get('complete') is not True or row.get('loaded_levels', 0) < 1:
            return {'result': 'INCONCLUSIVE', 'reason': 'INCOMPLETE_QUEUE_OBSERVATION'}
        queues = row.get('queues')
        if not isinstance(queues, dict) or not queues:
            return {'result': 'INCONCLUSIVE', 'reason': 'MISSING_QUEUE_COUNTERS'}
        if queue_keys is not None and set(queues) != queue_keys:
            return {'result': 'INCONCLUSIVE', 'reason': 'QUEUE_IDENTITY_CHANGED'}
        queue_keys = set(queues)
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in queues.values()):
            return {'result': 'INCONCLUSIVE', 'reason': 'INVALID_QUEUE_COUNTER'}
        for key in ('elapsed', 'cpu_one_core_pct', 'read_bytes_per_second', 'write_bytes_per_second'):
            value = row.get(key)
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or not math.isfinite(value) or value < 0):
                return {'result': 'INCONCLUSIVE', 'reason': 'INVALID_RESOURCE_COUNTER'}
        if not isinstance(row.get('database_fingerprint'), str) or len(row['database_fingerprint']) != 64:
            return {'result': 'INCONCLUSIVE', 'reason': 'MISSING_DATABASE_IDENTITY'}
        if sum(queues.values()) > max_backlog:
            return {'result': 'FAIL', 'reason': 'BOUNDED_BACKLOG_EXCEEDED'}
    if any(b['elapsed'] <= a['elapsed'] or b['elapsed'] - a['elapsed'] > 15
           for a, b in zip(samples, samples[1:])):
        return {'result': 'INCONCLUSIVE', 'reason': 'MISSING_OR_UNORDERED_OBSERVATIONS'}
    end = samples[-1]['elapsed']
    starts = [index for index, row in enumerate(samples) if row['elapsed'] <= end - quiet_seconds]
    window = samples[starts[-1]:] if starts else samples
    sufficiently_long = window[-1]['elapsed'] - window[0]['elapsed'] >= quiet_seconds
    quiet = (sufficiently_long and all(not any(row['queues'].values()) for row in window)
             and len({row['database_fingerprint'] for row in window}) == 1
             and statistics.mean(row['cpu_one_core_pct'] for row in window) <= 5
             and percentile([row['cpu_one_core_pct'] for row in window], .95) <= 10
             and percentile([row['read_bytes_per_second'] for row in window], .95) == 0
             and percentile([row['write_bytes_per_second'] for row in window], .95) == 0)
    if quiet and end <= timeout:
        return {'result': 'PASS', 'reason': 'STABLE_ZERO_QUEUES_DATABASE_AND_IDLE_RESOURCES',
                'converged_by_seconds': end, 'quiet_window_seconds': quiet_seconds}
    return {'result': 'FAIL' if end >= timeout else 'INCONCLUSIVE',
            'reason': 'CONVERGENCE_TIMEOUT' if end >= timeout else 'OBSERVATION_IN_PROGRESS'}
