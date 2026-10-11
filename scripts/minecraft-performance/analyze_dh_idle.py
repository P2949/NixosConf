"""Summarize paired DH idle data and sampled JFR attribution without waiving gates."""

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import statistics


def interval(values):
    rng = random.Random(261011)
    boot = sorted(statistics.median(rng.choices(values, k=len(values))) for _ in range(5000))
    return [boot[125], boot[4874]]


def stacks(path):
    events = json.loads(path.read_text())['recording']['events']
    counts = Counter()
    native = Counter()
    names = {}
    for event in events:
        value = event['values']
        thread = value.get('sampledThread') or value.get('eventThread') or {}
        tid = thread.get('osThreadId')
        if tid is not None:
            names[str(tid)] = thread.get('javaName') or thread.get('osName')
        if event['type'] not in ('jdk.ExecutionSample', 'jdk.NativeMethodSample'):
            continue
        for frame in (value.get('stackTrace') or {}).get('frames', []):
            method = frame.get('method') or {}
            owner = (method.get('type') or {}).get('name', '')
            target = counts if event['type'] == 'jdk.ExecutionSample' else native
            target[(names.get(str(tid), ''), owner + '.' + method.get('name', ''))] += 1
    return {'native_thread_names': names,
            'inclusive_stack_sample_counts': [dict(thread=t, method=m, samples=n)
                for (t, m), n in counts.most_common(80)],
            'native_stack_sample_counts': [dict(thread=t, method=m, samples=n)
                for (t, m), n in native.most_common(30)],
            'limitation': 'Execution stacks are sampled attribution, not exact CPU-time shares. '
                          'Native samples can include blocked I/O and are not CPU cost; '
                          'use measured native-thread CPU accounting to rank costs.'}


def analyze(root):
    results = json.loads((root / 'results.json').read_text())
    by_name = {r['variant']: r for r in results}
    pairs = []
    for i in range(1, 6):
        off, on = by_name[f'pair-{i}-off'], by_name[f'pair-{i}-on']
        pairs.append({'pair': i, 'off_cpu_pct': off['service_cpu_median_one_core_pct'],
                      'on_cpu_pct': on['service_cpu_median_one_core_pct'],
                      'off_power_w': off['package_power_w'], 'on_power_w': on['package_power_w'],
                      'power_delta_w': on['package_power_w'] - off['package_power_w']})
    power = [p['power_delta_w'] for p in pairs]
    cpu = [p['on_cpu_pct'] for p in pairs]
    result = {'pairs': pairs, 'median_on_cpu_pct': statistics.median(cpu),
              'median_paired_power_delta_w': statistics.median(power),
              'paired_power_delta_ci95_w': interval(power),
              'on_cpu_median_ci95_pct': interval(cpu),
              'resource_limits_pass': statistics.median(cpu) <= 5 and max(interval(power)) <= 1,
              'world_unchanged_all': all(r['world_unchanged'] for r in results),
              'memory_events_zero_all': all(not any(r['memory_events_delta'].values()) for r in results),
              'functional_recovery_and_queue_gates': 'REQUIRE_SEPARATE_REVIEW',
              'result': 'INCONCLUSIVE', 'diagnostics': [r for r in results if r['variant'].startswith('diagnostic')]}
    for evidence in root.glob('*-evidence'):
        data = stacks(evidence / 'jfr-events.json')
        (evidence / 'jfr-attribution.json').write_text(json.dumps(data, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    result = analyze(args.root)
    (args.root / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'diagnostics'}, indent=2))
