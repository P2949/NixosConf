"""C2ME decisions from independent runs; never relabel variants as collectors."""

import argparse
import json
import math
from pathlib import Path

# Reuse only the deterministic run-level statistical primitive. GC selection
# rules are deliberately not invoked by this adjudicator.
from analyze import comparison, credible

WORKLOADS = ('steady', 'worldgen', 'contention')
METRICS = {
    'steady': ('server_p95_mspt', 'ticks_over_50ms'),
    'worldgen': ('server_p95_mspt', 'ticks_over_50ms', 'worldgen_completion_seconds'),
    'contention': ('server_p95_mspt', 'ticks_over_50ms',
                   'worldgen_completion_seconds', 'client_1pct_fps'),
}


def decide(runs):
    def outcome(result, rule, **details):
        return {'result': result, 'decision': 'reject_C2ME' if result == 'FAIL' else None,
                'rule': rule, **details}

    variants = ('without_C2ME', 'C2ME_4')
    if not isinstance(runs, list) or not runs:
        return outcome('INCONCLUSIVE', 'missing_runs')
    if any(not isinstance(r, dict) or r.get('variant') not in variants
           or r.get('workload') not in WORKLOADS for r in runs):
        return outcome('INCONCLUSIVE', 'unknown_run_identity')
    for key in ('run_id', 'clone_uuid'):
        identities = [r.get(key) for r in runs]
        if any(not isinstance(v, str) or not v for v in identities) or len(set(identities)) != len(identities):
            return outcome('INCONCLUSIVE', 'duplicate_or_missing_run_identity', identity=key)
    for row in runs:
        events = row.get('memory_events')
        if isinstance(events, dict) and any(
                isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in events.values()):
            return outcome('INCONCLUSIVE', 'invalid_resource_evidence')
        if row.get('correctness') == 'FAIL' or (
                isinstance(events, dict) and any(events.get(k, 0) > 0
                    for k in ('oom', 'oom_kill', 'max'))) or row.get('severe_memory_high') is True:
            return outcome('FAIL' if row['variant'] == 'C2ME_4' else 'INCONCLUSIVE',
                           'candidate_disqualified' if row['variant'] == 'C2ME_4' else 'unsafe_control')
    comparisons = {}
    if any(not isinstance(r.get('valid'), bool) or
           r.get('correctness') not in ('PASS', 'FAIL', 'INCONCLUSIVE', 'BLOCKED') or
           (r['valid'] is False and not isinstance(r.get('invalid_reason'), str)) for r in runs):
        return outcome('INCONCLUSIVE', 'malformed_run_outcome')
    for workload in WORKLOADS:
        all_rows = [r for r in runs if r['workload'] == workload]
        # Input order is execution order, including rejected attempts. Require
        # both variants in every successive pair instead of grouped execution.
        if len(all_rows) % 2 or any({r['variant'] for r in all_rows[i:i + 2]} != set(variants)
                                  for i in range(0, len(all_rows), 2)):
            return outcome('INCONCLUSIVE', 'non_interleaved_execution', workload=workload)
        rows = {v: [r for r in all_rows if r['variant'] == v and r.get('valid') is True
                    and r.get('correctness') == 'PASS'] for v in variants}
        if any(len(rows[v]) < 5 for v in variants):
            return outcome('INCONCLUSIVE', 'insufficient_valid_runs', workload=workload)
        comparisons[workload] = {}
        for variant, entries in rows.items():
            for row in entries:
                events = row.get('memory_events')
                if not isinstance(events, dict) or any(k not in events or
                        isinstance(events[k], bool) or not isinstance(events[k], int) or events[k] < 0
                        for k in ('oom', 'oom_kill', 'max', 'high')) or row.get('severe_memory_high') is not False:
                    return outcome('INCONCLUSIVE', 'missing_resource_evidence', workload=workload)
                for key in METRICS[workload]:
                    value = row.get('metrics', {}).get(key)
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                        return outcome('INCONCLUSIVE', 'invalid_metric', workload=workload, metric=key)
                    if key != 'ticks_over_50ms' and value == 0:
                        return outcome('INCONCLUSIVE', 'invalid_metric', workload=workload, metric=key)
        for key in METRICS[workload]:
            comparisons[workload][key] = comparison(
                [r['metrics'][key] for r in rows['without_C2ME']],
                [r['metrics'][key] for r in rows['C2ME_4']])
    noninferiority = True
    server_noninferiority = True
    regressions = []
    benefits = []
    for workload, metrics in comparisons.items():
        for key, threshold, higher in (
                ('server_p95_mspt', 5, False),
                ('worldgen_completion_seconds', 3, False),
                ('client_1pct_fps', 2, True)):
            if key not in metrics:
                continue
            interval = metrics[key]['ci95']
            if interval is None:
                noninferiority = False
                if not higher:
                    server_noninferiority = False
            elif (interval[1] < -threshold if higher else interval[0] > threshold):
                regressions.append({'workload': workload, 'metric': key})
                if not higher:
                    server_noninferiority = False
            elif not (interval[0] >= -threshold if higher else interval[1] <= threshold):
                noninferiority = False
                if not higher:
                    server_noninferiority = False
        for key, threshold in (('worldgen_completion_seconds', 5),
                               ('server_p95_mspt', 5), ('ticks_over_50ms', 15)):
            if key in metrics and credible(metrics[key], threshold, False):
                benefits.append({'workload': workload, 'metric': key})
    if regressions:
        return outcome('FAIL', 'credible_regression', regressions=regressions,
                       comparisons=comparisons, benefits=benefits,
                       fallback_3_authorized=bool(server_noninferiority and benefits and
                           all(r == {'workload': 'contention', 'metric': 'client_1pct_fps'}
                               for r in regressions)))
    if not noninferiority:
        return outcome('INCONCLUSIVE', 'noninferiority_not_demonstrated', comparisons=comparisons)
    # No material benefit: retain the simpler accepted control. Do not force
    # adoption from a small/inconclusive speedup, even when it is safe.
    return {'result': 'PASS', 'decision': 'C2ME_4' if benefits else 'without_C2ME',
            'rule': 'material_benefit' if benefits else 'no_material_benefit',
            'benefits': benefits, 'comparisons': comparisons}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, required=True)
    args = parser.parse_args()
    result = decide(json.loads(args.runs.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit({'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}[result['result']])
