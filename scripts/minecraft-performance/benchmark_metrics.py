"""Summaries of bounded tick/frame/cgroup windows from disposable benchmarks."""

import csv
from datetime import datetime
import math
from pathlib import Path
import re
import statistics

from analyze import frame_summary, percentile
from idle_metrics import cpu_percent, host_cpu, io_delta


def read_window(path, start, end, column):
    if not 0 < start < end:
        raise ValueError('invalid measurement window')
    values = []
    times = []
    previous = 0
    with Path(path).open() as stream:
        for row in csv.DictReader(stream):
            stamp = int(row['monotonic_ns'])
            value = float(row[column])
            if stamp <= previous or not math.isfinite(value) or value < 0:
                raise ValueError('invalid or non-monotonic probe data')
            previous = stamp
            if start <= stamp / 1e9 <= end:
                times.append(stamp / 1e9)
                values.append(value)
    if len(values) < 100 or times[-1] - times[0] < (end - start) * .95:
        raise ValueError('incomplete probe measurement window')
    return values


def tick_metrics(path, start, end):
    values = read_window(path, start, end, 'tick_ms')
    return {'server_median_mspt': percentile(values, .5),
            'server_p95_mspt': percentile(values, .95),
            'server_p99_mspt': percentile(values, .99),
            'ticks_over_50ms': sum(v > 50 for v in values), 'tick_count': len(values)}


def client_metrics(path, start, end):
    return frame_summary(read_window(path, start, end, 'frame_ms'))


def resource_metrics(samples, start, end, cpu_count, memory_high_bytes):
    rows = [s for s in samples if start <= s['time'] <= end]
    if len(rows) < 3 or rows[-1]['time'] - rows[0]['time'] < (end - start) * .95:
        raise ValueError('incomplete resource measurement window')
    if cpu_count <= 0:
        raise ValueError('invalid host CPU count')
    service = []
    unrelated = []
    high_streak = longest_high = 0
    for before, after in zip(rows, rows[1:]):
        dt = after['time'] - before['time']
        s = cpu_percent(before['service_us'], after['service_us'], dt)
        c = cpu_percent(before['client_us'], after['client_us'], dt)
        service.append(s)
        unrelated.append(max(0, host_cpu(before['host_cpu'], after['host_cpu']) - (s + c) / cpu_count))
        high_streak = high_streak + 1 if after['memory_bytes'] >= memory_high_bytes else 0
        longest_high = max(longest_high, high_streak)
    events = {key: rows[-1]['memory_events'][key] - rows[0]['memory_events'][key]
              for key in rows[0]['memory_events']}
    if any(v < 0 for v in events.values()):
        raise ValueError('memory event counter reset')
    return {'cpu_pct': statistics.mean(service),
            'cpu_p95_pct': percentile(service, .95),
            'memory_peak_bytes': max(s['memory_bytes'] for s in rows),
            'memory_events': events,
            'severe_memory_high': longest_high >= 10 and events.get('high', 0) > 0,
            'io': io_delta(rows[0]['io'], rows[-1]['io']),
            'unrelated_host_median_pct': statistics.median(unrelated),
            'unrelated_host_p95_pct': percentile(unrelated, .95),
            'unrelated_host_maximum_pct': max(unrelated),
            'environment_valid': percentile(unrelated, .95) <= 5 and max(unrelated) <= 20}


def jfr_gc_metrics(recording, start_utc, end_utc):
    counts = pauses = 0
    total_pause_ms = 0
    for event in recording['recording']['events']:
        values = event['values']
        stamp = datetime.fromisoformat(values['startTime'].replace('Z', '+00:00')).timestamp()
        if not start_utc <= stamp <= end_utc:
            continue
        if event['type'] == 'jdk.GarbageCollection':
            counts += 1
        elif event['type'] == 'jdk.GCPhasePause':
            duration = values['duration']
            if isinstance(duration, int) and not isinstance(duration, bool):
                milliseconds = duration / 1e6
            elif isinstance(duration, str) and (match := re.fullmatch(r'PT([0-9.]+)S', duration)):
                milliseconds = float(match[1]) * 1000
            else:
                raise ValueError('unsupported JFR duration schema')
            if not math.isfinite(milliseconds) or milliseconds < 0:
                raise ValueError('invalid JFR duration')
            total_pause_ms += milliseconds
            pauses += 1
    return {'gc_collections': counts, 'gc_pause_count': pauses, 'gc_pause_total_ms': total_pause_ms}
