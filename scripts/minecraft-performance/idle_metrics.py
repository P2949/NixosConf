"""Pure, fail-closed arithmetic for clean Minecraft idle qualification."""

import math
import statistics


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('non-finite or non-numeric measurement')
    return value


def percentile(values, fraction):
    values = sorted(finite(v) for v in values)
    if not values:
        raise ValueError('missing samples')
    position = (len(values) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def distribution(values):
    return {'median': statistics.median(values), 'p95': percentile(values, .95),
            'maximum': max(values)}


def rapl_delta(before, after, maximum, seconds):
    before, after, maximum, seconds = map(finite, (before, after, maximum, seconds))
    if maximum <= 0 or seconds <= 0 or not 0 <= before < maximum or not 0 <= after < maximum:
        raise ValueError('invalid RAPL range, reading or interval')
    if after < before and not (before >= .9 * maximum and after <= .1 * maximum):
        raise ValueError('RAPL reset or unexpected counter decrease')
    delta = (after - before) % maximum
    if delta / 1e6 / seconds > 250:
        raise ValueError('RAPL delta exceeds physical preflight ceiling of 250 W')
    return delta


def cpu_percent(before, after, seconds):
    before, after, seconds = map(finite, (before, after, seconds))
    if seconds <= 0 or after < before:
        raise ValueError('CPU counter reset or invalid interval')
    return (after - before) / seconds / 10000


def host_cpu(before, after):
    def fields(value):
        tokens = value.split()
        if tokens[0] != 'cpu' or len(tokens) < 9:
            raise ValueError('invalid aggregate host CPU row')
        return list(map(int, tokens[1:9]))
    delta = [b - a for a, b in zip(fields(before), fields(after))]
    if any(v < 0 for v in delta) or sum(delta) <= 0:
        raise ValueError('host CPU reset or empty interval')
    return 100 * (sum(delta) - delta[3] - delta[4]) / sum(delta)


def io_counters(value):
    result = {}
    for line in value.splitlines():
        tokens = line.split()
        if tokens[0] in result:
            raise ValueError('duplicate I/O device')
        result[tokens[0]] = {k: int(v) for k, v in (t.split('=') for t in tokens[1:])}
    return result


def io_delta(before, after):
    before, after = io_counters(before), io_counters(after)
    result = {k: 0 for k in ('rbytes', 'wbytes', 'rios', 'wios', 'dbytes', 'dios')}
    if not set(before).issubset(after):
        raise ValueError('I/O device counter disappeared')
    for device, counters in after.items():
        for key in result:
            delta = counters.get(key, 0) - before.get(device, {}).get(key, 0)
            if delta < 0:
                raise ValueError('I/O counter reset')
            result[key] += delta
    return result


def unique_java(candidates):
    if len(candidates) != 1:
        raise ValueError('unit must contain exactly one Java process')
    return candidates[0]


def validate_rapl(name, enabled, maximum):
    if name != 'package-0' or enabled != 1 or maximum <= 0:
        raise ValueError('expected enabled Intel CPU package-0 energy zone')


def summarize(rows, maximum, logical_cpus):
    if len(rows) < 2 or logical_cpus <= 0:
        raise ValueError('missing fixed-interval samples')
    cpu, unrelated, watts, reads, writes = [], [], [], [], []
    for a, b in zip(rows, rows[1:]):
        dt = b['time'] - a['time']
        cpu.append(cpu_percent(a['cpu']['usage_usec'], b['cpu']['usage_usec'], dt))
        unrelated.append(max(0, host_cpu(a['host_cpu'], b['host_cpu']) - cpu[-1] / logical_cpus))
        watts.append(rapl_delta(a['energy_uj'], b['energy_uj'], maximum, dt) / 1e6 / dt)
        io = io_delta(a['io'], b['io'])
        reads.append(io['rbytes'] / dt)
        writes.append(io['wbytes'] / dt)
    a, b = rows[0], rows[-1]
    duration = b['time'] - a['time']
    events = {k: b['memory_events'][k] - v for k, v in a['memory_events'].items()}
    if any(v < 0 for v in events.values()):
        raise ValueError('memory event counter reset')
    return {'duration': duration,
            'service_cpu_interval_one_core_pct': cpu_percent(a['cpu']['usage_usec'], b['cpu']['usage_usec'], duration),
            'service_cpu_median_one_core_pct': statistics.median(cpu),
            'service_cpu_distribution_one_core_pct': distribution(cpu),
            'unrelated_host_cpu_pct': distribution(unrelated),
            'package_power_w': sum(w * (y['time'] - x['time']) for w, x, y in zip(watts, rows, rows[1:])) / duration,
            'package_power_distribution_w': distribution(watts),
            'memory_events_delta': events,
            'io_delta': io_delta(a['io'], b['io']),
            'io_read_bytes_s': distribution(reads), 'io_write_bytes_s': distribution(writes),
            'io_sustained_pass': percentile(reads, .95) == 0 and percentile(writes, .95) == 0,
            'host_load_pass': percentile(unrelated, .95) <= 5 and max(unrelated) <= 20}


def indexed_pairs(rows, expected_pair_count=5):
    if expected_pair_count not in (5, 7, 9, 11):
        raise ValueError('paired qualification requires 5, 7, 9, or 11 pairs')
    def numeric_values(value, key=None):
        if isinstance(value, bool) and key in ('environment_clients_absent', 'world_unchanged',
                                               'host_load_pass', 'outside_client_seen', 'io_sustained_pass'):
            return
        if isinstance(value, (int, float)):
            finite(value)
        elif isinstance(value, dict):
            for name, item in value.items():
                numeric_values(item, name)
        elif isinstance(value, list):
            for item in value:
                numeric_values(item)
    indexed = {}
    for row in rows:
        numeric_values(row)
        name = row['variant']
        if name in indexed:
            raise ValueError('duplicate variant: ' + name)
        indexed[name] = row
        for key in ('service_cpu_interval_one_core_pct', 'package_power_w'):
            finite(row[key])
    expected = {f'pair-{i}-{v}' for i in range(1, expected_pair_count + 1) for v in ('off', 'on')}
    if set(indexed) != expected:
        raise ValueError('missing or unexpected paired variants')
    return [(indexed[f'pair-{i}-off'], indexed[f'pair-{i}-on']) for i in range(1, expected_pair_count + 1)]


def pair_invalidity_reasons(off, on):
    reasons = []
    for variant, row in (('off', off), ('on', on)):
        checks = {
            'mode_not_clean': row['mode'] == 'clean',
            'duration_below_599_seconds': row['duration'] >= 599,
            'minecraft_client_overlap': row['environment_clients_absent'],
            'host_p95_above_5_percent': row['unrelated_host_cpu_pct']['p95'] <= 5,
            'host_maximum_above_20_percent': row['unrelated_host_cpu_pct']['maximum'] <= 20,
            'host_load_gate_failed': row['host_load_pass'],
        }
        reasons.extend(variant + ':' + name for name, passed in checks.items() if not passed)
    # Remove measured benchmark CPU before comparing the unrelated host load.
    if abs(off['unrelated_host_cpu_pct']['median'] - on['unrelated_host_cpu_pct']['median']) > .5:
        reasons.append('unrelated_host_median_difference_above_0_5_percentage_points')
    return reasons


def pair_valid(off, on):
    return not pair_invalidity_reasons(off, on)


def pair_io_pass(off, on):
    # The control exposes unavoidable JVM hsperfdata writeback (~4 KiB/30 s).
    # Permit at most four additional metadata pages, never sustained I/O or DB mutation.
    return on['io_delta']['rbytes'] <= off['io_delta']['rbytes'] and \
        on['io_delta']['wbytes'] <= off['io_delta']['wbytes'] + 16384 and \
        on['io_delta']['dbytes'] == off['io_delta']['dbytes'] == 0
