"""Summarize paired DH idle data and sampled JFR attribution without waiving gates."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics

from idle_metrics import indexed_pairs, pair_io_pass, pair_valid
from qualification_manifest import verify_proof
from assemble_functional_acceptance import REQUIRED, verify_bundle

FIXED_PAIRS = 11


def verified_gate(gate, gate_name=None, manifest=None):
    return verify_proof(gate, gate_name, manifest)


def paired_mean_interval(values):
    if len(values) != FIXED_PAIRS or not all(math.isfinite(value) for value in values):
        raise ValueError('one fixed batch of eleven finite paired deltas required')
    # NIST mean CI: mean +/- t(.975, df=10) * sample SD / sqrt(11).
    # Rounded slightly upward; inferential assumptions are recorded in output.
    half_width = 2.228139 * statistics.stdev(values) / math.sqrt(FIXED_PAIRS)
    mean = statistics.mean(values)
    return [mean - half_width, mean + half_width]


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


def analyze(root, expected_pair_count=FIXED_PAIRS, functional_bundle=None):
    if expected_pair_count != FIXED_PAIRS:
        raise ValueError('authoritative analysis requires the predeclared eleven pairs')
    results = json.loads((root / 'results.json').read_text())
    pairs = []
    clean = [r for r in results if r['variant'].startswith('pair-')]
    paired = indexed_pairs(clean, expected_pair_count)
    for i, (off, on) in enumerate(paired, 1):
        pairs.append({'pair': i, 'off_cpu_pct': off['service_cpu_interval_one_core_pct'],
                      'on_cpu_pct': on['service_cpu_interval_one_core_pct'],
                      'off_power_w': off['package_power_w'], 'on_power_w': on['package_power_w'],
                      'power_delta_w': on['package_power_w'] - off['package_power_w'],
                      'environment_valid': pair_valid(off, on), 'io_valid': pair_io_pass(off, on)})
    power = [p['power_delta_w'] for p in pairs]
    cpu = [p['on_cpu_pct'] for p in pairs]
    burst = [on['service_cpu_distribution_one_core_pct']['p95'] for off, on in paired]
    power_interval = paired_mean_interval(power)
    power_result = 'PASS' if power_interval[1] <= 1 else (
        'FAIL' if power_interval[0] > 1 else 'INCONCLUSIVE')
    result = {'pairs': pairs, 'median_on_interval_cpu_pct': statistics.median(cpu),
              'median_on_p95_cpu_pct': statistics.median(burst),
              'median_paired_power_delta_w': statistics.median(power),
              'mean_paired_power_delta_w': statistics.mean(power),
              'paired_power_deltas_w': power,
              'paired_power_delta_range_w': [min(power), max(power)],
              'paired_power_delta_ci95_w': power_interval,
              'power_acceptance': power_result,
              'pair_count': expected_pair_count,
              'statistical_design': {'fixed_pairs': FIXED_PAIRS, 'interim_inferential_looks': 0,
                  'primary_estimand': 'mean paired DH-on minus DH-off package power',
                  'interval_method': 'two-sided Student t, df=10, nominal 95%',
                  'assumptions': 'independent matched-pair deltas with approximately normal run means; '
                                 'fixed sampling does not remove host confounding or model uncertainty',
                  'reference': 'https://itl.nist.gov/div898/handbook/eda/section3/eda352.htm'},
              'resource_limits_pass': statistics.median(cpu) <= 5 and statistics.median(burst) <= 10 and power_interval[1] <= 1,
              'host_load_pass': all(p['environment_valid'] for p in pairs),
              'io_pass': all(p['io_valid'] and off['io_sustained_pass'] and on['io_sustained_pass']
                             for p, (off, on) in zip(pairs, paired)),
              'world_unchanged_all': all(r['world_unchanged'] for r in clean),
              'memory_events_zero_all': all(not any(r['memory_events_delta'].values()) for r in clean),
              'functional_recovery_and_queue_gates': 'REQUIRE_SEPARATE_REVIEW',
              'result': 'INCONCLUSIVE', 'diagnostics': [r for r in results if r['variant'].startswith('diagnostic')]}
    gates = ('resource_limits_pass', 'host_load_pass', 'io_pass', 'world_unchanged_all', 'memory_events_zero_all')
    definite_failure = (statistics.median(cpu) > 5 or statistics.median(burst) > 10
                        or power_result == 'FAIL' or not result['io_pass']
                        or not result['world_unchanged_all'] or not result['memory_events_zero_all'])
    result['idle_acceptance'] = ('INCONCLUSIVE' if not result['host_load_pass'] else
        'FAIL' if definite_failure else 'PASS' if all(result[k] for k in gates) else 'INCONCLUSIVE')
    receipt = Path(functional_bundle) if functional_bundle is not None else root / 'functional-acceptance.json'
    acceptance = json.loads(receipt.read_text()) if receipt.exists() else {}
    manifest_path = root / 'candidate-manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    result['functional_gates'] = verify_bundle(acceptance, manifest) if manifest else {k: 'UNPROVEN' for k in REQUIRED}
    if result['idle_acceptance'] == 'FAIL' or 'FAIL' in result['functional_gates'].values():
        result['result'] = 'FAIL'
    if result['idle_acceptance'] == 'PASS' and all(v == 'PASS' for v in result['functional_gates'].values()):
        result['result'] = 'PASS'
    for evidence in root.glob('*-evidence'):
        recording = evidence / 'jfr-events.json'
        if recording.exists():
            data = stacks(recording)
            (evidence / 'jfr-attribution.json').write_text(json.dumps(data, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--idle-run', type=Path, required=True)
    parser.add_argument('--functional-bundle', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.idle_run, functional_bundle=args.functional_bundle)
    (args.idle_run / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'diagnostics'}, indent=2))

    raise SystemExit({'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}[result['result']])
