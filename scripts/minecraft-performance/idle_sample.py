"""Collect a bounded, one-second idle acceptance sample from a verified unit."""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

from analyze import percentile


def pairs(path):
    return {k: int(v) for k, v in (line.split() for line in path.read_text().splitlines())}


def summary(values):
    return {'median': percentile(values, .5), 'p95': percentile(values, .95), 'maximum': max(values)}


def collect(unit, output, duration, warmup):
    subprocess.run(['systemctl', 'is-active', '--quiet', unit], check=True)
    group = subprocess.check_output(['systemctl', 'show', unit, '-p', 'ControlGroup', '--value'], text=True).strip()
    cgroup = (Path('/sys/fs/cgroup') / group.lstrip('/')).resolve()
    if not cgroup.is_relative_to(Path('/sys/fs/cgroup')) or not group:
        raise ValueError('invalid cgroup path')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for _ in range(warmup):
        subprocess.run(['systemctl', 'is-active', '--quiet', unit], check=True)
        time.sleep(1)
    candidates = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            membership = process.joinpath('cgroup').read_text().splitlines()
            command = process.joinpath('cmdline').read_bytes().split(b'\0')
            if any(line.endswith(':' + group) for line in membership) and command[0].endswith(b'/bin/java'):
                candidates.append(process)
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    if len(candidates) != 1:
        raise ValueError('unit must contain exactly one Java process')
    process = candidates[0]
    hz = os.sysconf('SC_CLK_TCK')

    def sample():
        if not any(line.endswith(':' + group) for line in process.joinpath('cgroup').read_text().splitlines()):
            raise ValueError('Java process left the expected unit')
        stat = process.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
        status = process.joinpath('status').read_text().splitlines()
        rss = int(next(line.split()[1] for line in status if line.startswith('VmRSS:'))) * 1024
        return {'monotonic': time.monotonic(), 'utc': time.time(),
                'service_us': pairs(cgroup / 'cpu.stat')['usage_usec'],
                'process_ticks': int(stat[11]) + int(stat[12]), 'rss_bytes': rss,
                'memory_bytes': int((cgroup / 'memory.current').read_text()),
                'memory_events': pairs(cgroup / 'memory.events'),
                'system_cpu': list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:])),
                'diskstats': Path('/proc/diskstats').read_text()}

    rows = [sample()]
    with (output / 'samples.jsonl').open('w') as stream:
        stream.write(json.dumps(rows[0]) + '\n')
        for i in range(duration):
            time.sleep(max(0, rows[0]['monotonic'] + i + 1 - time.monotonic()))
            rows.append(sample())
            stream.write(json.dumps(rows[-1]) + '\n')
            stream.flush()
    metrics = {'service_cpu_one_core_pct': [], 'process_cpu_one_core_pct': [], 'system_cpu_pct': [],
               'rss_bytes': [row['rss_bytes'] for row in rows],
               'memory_current_bytes': [row['memory_bytes'] for row in rows]}
    for a, b in zip(rows, rows[1:]):
        dt = b['monotonic'] - a['monotonic']
        metrics['service_cpu_one_core_pct'].append((b['service_us'] - a['service_us']) / dt / 10000)
        metrics['process_cpu_one_core_pct'].append((b['process_ticks'] - a['process_ticks']) / hz / dt * 100)
        cpu = [y - x for x, y in zip(a['system_cpu'][:8], b['system_cpu'][:8])]
        metrics['system_cpu_pct'].append(100 * (sum(cpu) - cpu[3] - cpu[4]) / sum(cpu))
    result = {key: summary(values) for key, values in metrics.items()}
    result['memory_event_delta'] = {key: rows[-1]['memory_events'][key] - rows[0]['memory_events'][key]
                                    for key in rows[0]['memory_events']}
    result['duration_seconds'] = rows[-1]['monotonic'] - rows[0]['monotonic']
    result['unit'] = unit
    result['java_pid'] = int(process.name)
    result['result'] = 'PASS' if result['service_cpu_one_core_pct']['median'] <= 1 and all(
        result['memory_event_delta'][key] == 0 for key in ('max', 'oom', 'oom_kill')) else 'FAIL'
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    for file in output.iterdir():
        file.chmod(0o600)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unit', default='minecraft-server-survival.service')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--duration', type=int, default=300)
    parser.add_argument('--warmup', type=int, default=90)
    args = parser.parse_args()
    if args.duration < 300 or args.warmup < 90:
        parser.error('acceptance requires at least 300 measured seconds and 90 stabilization seconds')
    result = collect(args.unit, args.output, args.duration, args.warmup)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['result'] == 'PASS' else 1)
