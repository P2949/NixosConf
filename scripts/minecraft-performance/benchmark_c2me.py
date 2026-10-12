"""Fixed interleaved C2ME trials on fresh clones, with independent safe recovery."""

import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time

from analyze_c2me import WORKLOADS, decide
from assemble_functional_acceptance import verify_bundle
from benchmark_metrics import client_metrics, jfr_gc_metrics, resource_metrics, tick_metrics
from client_runtime import Client
from dh_idle_attribution import counters, minecraft_clients, save
from functional_dh import dh_outcome, generation_outcome, read_dh_messages
from functional_runtime import Lab, command
from generate_candidate_manifest import baseline_identity
from post_chunky import chunk_bounds, generation_extent, require_ungenerated
from qualification_manifest import canonical_bytes, controlled_path, qualification_id, sha256, validate_candidate
from world_semantics import region_occupancy
import maintenance

HERE = Path(__file__).resolve().parent
PAIRS = 5
RADIUS = 1024
CENTER = 8192
WINDOW = 90
WARMUP = 30
CLIENT_DURATION = 150
ENVIRONMENT_RETRIES = 3
COMPLETION = re.compile(r'Task finished for minecraft:overworld\. Processed: ([\d,]+) chunks \(100\.00%\)')


class BenchmarkInterrupted(RuntimeError):
    pass


class RunFailure(RuntimeError):
    def __init__(self, receipt):
        super().__init__('disposable benchmark run failed')
        self.receipt = receipt


def trial_directory(study, workload, pair, attempt, variant):
    identity = study.name.removeprefix('minecraft-performance-functional-c2me-study-')
    if not re.fullmatch(r'[A-Za-z0-9-]{1,20}', identity):
        raise ValueError('bounded ASCII study identity required')
    label = {'steady': 's', 'worldgen': 'w', 'contention': 'c'}[workload]
    variant_label = {'without_C2ME': 'A', 'C2ME_4': 'B'}[variant]
    path = study.parent / f'minecraft-performance-functional-c2me-{identity}-{label}{pair + 1}-r{attempt}-{variant_label}'
    if len(str(path / 'world-clone/console.sock').encode()) >= 108:
        raise ValueError('benchmark console exceeds Linux UNIX socket path limit')
    return path


def pilot_decision(row):
    unsafe = (row['correctness'] == 'FAIL' or row['severe_memory_high'] or
              any(row['memory_events'].get(k, 0) > 0 for k in ('oom', 'oom_kill', 'max')))
    return {'result': 'FAIL' if unsafe else 'INCONCLUSIVE', 'decision': None,
            'rule': 'pilot_only_not_adoption',
            'pilot_outcome': 'FAIL' if unsafe else 'PASS' if row['valid'] and row['correctness'] == 'PASS' else 'INCONCLUSIVE',
            'generation_seconds': row.get('metrics', {}).get('worldgen_completion_seconds')}


def collect_trial_pair(workload, pair, execute_run, results):
    for attempt in range(ENVIRONMENT_RETRIES + 1):
        order = ('without_C2ME', 'C2ME_4') if (pair + attempt) % 2 == 0 else ('C2ME_4', 'without_C2ME')
        rows = []
        for variant in order:
            row = execute_run(workload, pair, attempt, variant)
            if any(row['memory_events'].get(k, 0) for k in ('oom', 'oom_kill', 'max')) or row['severe_memory_high']:
                row.update(correctness='FAIL', invalid_reason='resource_disqualification')
                raise RunFailure(row)
            rows.append(row)
            results.append(row)
        if all(row['valid'] for row in rows):
            return None
        environmental = all(row['valid'] or set(row['invalid_reason'].split(',')) <= {
            'unrelated_host_load', 'outside_minecraft_client_overlap'} for row in rows)
        for row in rows:
            row['individual_valid'] = row['valid']
            row['valid'] = False
            if not row['invalid_reason']:
                row['invalid_reason'] = 'paired_environment_rejection' if environmental else 'paired_workload_rejection'
        if not environmental:
            return 'workload_window_not_representative'
    return 'environment_retries_exhausted'


def same_stack(control, candidate, accepted):
    for field in ('git_sha', 'java', 'wrapper', 'jvm_flags', 'service', 'baseline',
                  'client', 'controlled_server_properties', 'server_tick_probe', 'generation_bounds'):
        if control.get(field) != candidate.get(field):
            raise ValueError('A/B identity differs: ' + field)
    if not control.get('server_tick_probe') or '-XX:+UseG1GC' not in control['jvm_flags']:
        raise ValueError('fixed G1 and source-verified tick probe required')
    for key in ('mods', 'pregen_mods'):
        without = [m for m in candidate[key] if m['id'] != 'c2me']
        if any(m['id'] == 'c2me' for m in control[key]) or without != control[key]:
            raise ValueError('A/B non-C2ME inventory differs')
    if {k: v for k, v in candidate['policies'].items() if k != 'config/c2me.toml'} != control['policies']:
        raise ValueError('A/B non-C2ME policy differs')
    for field in ('java', 'wrapper', 'mods', 'pregen_mods', 'policies', 'jvm_flags',
                  'service', 'baseline', 'client', 'controlled_server_properties',
                  'pregen_policy', 'pregen_pause_seconds'):
        if candidate.get(field) != accepted.get(field):
            raise ValueError('benchmark differs from qualified C2ME stack: ' + field)
    if control['pregen_policy'] != candidate['pregen_policy'] or control['pregen_pause_seconds'] != candidate['pregen_pause_seconds']:
        raise ValueError('A/B maintenance policy differs')


class Samples:
    def __init__(self, lab):
        self.lab = lab
        self.rows = []
        self.client_group = None
        self.client_us = 0
        self.error = None
        self.done = threading.Event()
        self.worker = threading.Thread(target=self.collect, daemon=True)

    def collect(self):
        try:
            while not self.done.is_set():
                if self.client_group is not None and self.client_group.exists():
                    try:
                        self.client_us = max(self.client_us, counters(self.client_group / 'cpu.stat')['usage_usec'])
                    except FileNotFoundError:
                        # The bounded client can exit between the existence
                        # check and the read. Retain its final observed count.
                        pass
                cg = self.lab.cgroup
                self.rows.append({'time': time.monotonic(), 'utc': time.time(),
                    'service_us': counters(cg / 'cpu.stat')['usage_usec'], 'client_us': self.client_us,
                    'host_cpu': Path('/proc/stat').read_text().splitlines()[0],
                    'memory_bytes': int((cg / 'memory.current').read_text()),
                    'memory_peak_bytes': int((cg / 'memory.peak').read_text()),
                    'memory_events': counters(cg / 'memory.events'), 'io': (cg / 'io.stat').read_text()})
                self.done.wait(1)
        except BaseException as exc:
            self.error = exc

    def start(self):
        self.worker.start()

    def stop(self):
        self.done.set()
        self.worker.join(5)
        if self.worker.is_alive() or self.error is not None:
            raise RuntimeError('resource sampling failed') from self.error


def wait_until(deadline, lab):
    while time.monotonic() < deadline:
        if not Path(f'/proc/{lab.pid}').exists():
            raise RuntimeError('benchmark server exited')
        maintenance.refresh()
        time.sleep(min(1, max(0, deadline - time.monotonic())))


def run_one(manifest, output, workload, variant):
    lab = Lab(manifest, output)
    (output / 'candidate-manifest.json').write_bytes(canonical_bytes(manifest))
    clone = command('btrfs', 'subvolume', 'show', str(lab.root))
    clone_uuid = re.search(r'^\s*UUID:\s*(\S+)', clone, re.MULTILINE)[1]
    receipt = {'run_id': output.name, 'clone_uuid': clone_uuid,
        'variant': variant, 'workload': workload, 'git_sha': manifest['git_sha'],
        'qualification_id': qualification_id(manifest), 'valid': False,
        'correctness': 'INCONCLUSIVE', 'invalid_reason': 'not_completed'}
    sampler = None
    outside_clients_before = bool(minecraft_clients())
    try:
        with lab:
            before = region_occupancy(lab.server / 'world', include_status=True)
            if workload != 'steady':
                require_ungenerated(before, chunk_bounds(CENTER, CENTER, RADIUS))
            lab.start(pregen=workload != 'steady')
            sampler = Samples(lab)
            sampler.start()
            client = None
            if workload != 'worldgen':
                client = Client(manifest, output / 'client', 'dh-clean', CLIENT_DURATION, fresh_cache=True)
                client.start()
                client.wait_joined()
                group = command('systemctl', 'show', maintenance.CLIENT, '-p', 'ControlGroup', '--value')
                sampler.client_group = Path('/sys/fs/cgroup') / group.lstrip('/')
                lab.send('gamemode spectator @a[name=PerfProbe,limit=1]')
                lab.send('tp @a[name=PerfProbe,limit=1] 0 100 0 0 0')
            wait_until(time.monotonic() + WARMUP, lab)
            start = time.monotonic()
            start_utc = time.time()
            completed = None
            completion_time = None
            if workload != 'steady':
                lab.send(f'chunky start minecraft:overworld square {CENTER} {CENTER} {RADIUS}')
                deadline = start + 1200
                while not (completed := COMPLETION.search(lab.log.read_text())):
                    if time.monotonic() > deadline or not Path(f'/proc/{lab.pid}').exists():
                        raise RuntimeError('worldgen completion failed')
                    maintenance.refresh()
                    time.sleep(.2)
                completion_time = time.monotonic()
                if workload == 'contention' and completion_time - start < WINDOW:
                    receipt['invalid_reason'] = 'generation_shorter_than_fixed_client_window'
            else:
                wait_until(start + WINDOW + 1, lab)
            end = completion_time if workload == 'worldgen' else start + WINDOW
            end_utc = start_utc + end - start
            if client is not None:
                client.wait_finished()
                if dh_outcome(read_dh_messages(client.output / 'dh-messages.jsonl'), manifest) != 'PASS':
                    raise RuntimeError('benchmark DH protocol failure')
            sampler.stop()
            rows = sampler.rows
            sampler = None
            save(output / 'samples.json', rows)
            lab.stop()
            after = region_occupancy(lab.server / 'world', include_status=True)
            if workload == 'steady':
                if generation_outcome(before, after, manifest) != 'PASS':
                    raise RuntimeError('steady workload generated unwanted terrain')
            else:
                extent = generation_extent(before, after, chunk_bounds(CENTER, CENTER, RADIUS),
                                           manifest['generation_bounds']['dependency_radius_chunks'])
                save(output / 'generation-extent.json', extent)
                expected = (2 * RADIUS // 16 + 1) ** 2
                if extent['result'] != 'PASS' or extent['new_full_chunks'] != int(completed[1].replace(',', '')) or extent['new_full_chunks'] != expected:
                    raise RuntimeError('worldgen structural/extent validation failed')
            text = lab.log.read_text()
            if any(s in text for s in ('Mixin apply failed', 'MixinTransformerError', 'OutOfMemoryError',
                    'Server Watchdog', 'Exception in server tick loop', 'Accessing LegacyRandomSource from multiple threads',
                    'Failed to read chunk', 'Failed to save chunk')):
                raise RuntimeError('server correctness log failure')
            # Sampling is stopped before the cgroup disappears. Keep all raw
            # samples in memory during the timed window, then persist once.
            resources = resource_metrics(rows, start, end, os.cpu_count(), 10 * 1024 ** 3)
            whole_run = resource_metrics(rows, rows[0]['time'], rows[-1]['time'], os.cpu_count(), 10 * 1024 ** 3)
            metrics = tick_metrics(lab.tick_output, start, end)
            metrics.update({k: resources[k] for k in ('cpu_pct', 'cpu_p95_pct', 'memory_peak_bytes', 'io')})
            metrics['service_lifetime_memory_peak_bytes'] = rows[-1]['memory_peak_bytes']
            jfr_json = output / 'gc-events.json'
            if lab.jfr_output.stat().st_size == 0:
                raise RuntimeError('JFR recording missing')
            with jfr_json.open('w') as stream:
                subprocess.run([str(Path(manifest['diagnostic_java_home']) / 'bin/jfr'), 'print', '--json',
                    '--events', 'jdk.GarbageCollection,jdk.GCPhasePause', str(lab.jfr_output)],
                    stdout=stream, check=True)
            metrics.update(jfr_gc_metrics(json.loads(jfr_json.read_text()), start_utc, end_utc))
            if client is not None:
                metrics.update(client_metrics(client.output / 'client-frametimes.csv', start, end))
            if completed is not None:
                metrics['worldgen_completion_seconds'] = completion_time - start
                metrics['worldgen_throughput'] = int(completed[1].replace(',', '')) / (completion_time - start)
            reasons = []
            if not resources['environment_valid']:
                reasons.append('unrelated_host_load')
            if outside_clients_before or minecraft_clients():
                reasons.append('outside_minecraft_client_overlap')
            if receipt['invalid_reason'] != 'not_completed':
                reasons.append(receipt['invalid_reason'])
            receipt.update(correctness='PASS', valid=not reasons, invalid_reason=','.join(reasons),
                metrics=metrics, memory_events=rows[-1]['memory_events'],
                severe_memory_high=whole_run['severe_memory_high'], environment=resources,
                measurement_start_monotonic=start, measurement_end_monotonic=end,
                measurement_start_utc=start_utc, measurement_end_utc=end_utc,
                evidence_sha256={str(p.relative_to(output)): sha256(p) for p in (
                    lab.log, lab.tick_output, lab.jfr_output, output / 'samples.json', jfr_json)})
            if client is not None:
                receipt['evidence_sha256'].update({str(p.relative_to(output)): sha256(p)
                    for p in (client.output / 'client-frametimes.csv', client.output / 'dh-messages.jsonl',
                              client.output / 'result.json', client.output / 'heartbeat.json', client.output / 'launcher.log')})
            save(output / 'run.json', receipt)
    except BaseException as exc:
        if sampler is not None:
            try:
                sampler.stop()
            except BaseException:
                pass
            save(output / 'samples.json', list(sampler.rows))
        receipt['correctness'] = 'INCONCLUSIVE' if isinstance(exc, BenchmarkInterrupted) else 'FAIL'
        receipt['invalid_reason'] = 'interrupted' if isinstance(exc, BenchmarkInterrupted) else 'runtime_or_correctness_failure'
        save(output / 'run.json', receipt)
        raise RunFailure(receipt) from exc
    return receipt


def execute(args):
    manifests = {v: json.loads(p.read_text()) for v, p in
        [('without_C2ME', args.control_manifest), ('C2ME_4', args.candidate_manifest)]}
    candidate = manifests['C2ME_4']
    for manifest in manifests.values():
        validate_candidate(manifest, HERE.parent.parent)
    accepted = json.loads(args.correctness_manifest.read_text())
    bundle = json.loads(args.correctness_bundle.read_text())
    if set(verify_bundle(bundle, accepted).values()) != {'PASS'}:
        raise ValueError('authentic C2ME correctness bundle required')
    same_stack(manifests['without_C2ME'], candidate, accepted)
    if baseline_identity(Path(candidate['baseline']['path'])) != candidate['baseline']:
        raise ValueError('benchmark baseline changed')
    output = controlled_path(args.output, Path('/persist'))
    if output.parent != Path('/persist') or not output.name.startswith('minecraft-performance-functional-c2me-study-'):
        raise ValueError('private direct benchmark namespace required')
    output.mkdir(mode=0o700)
    (output / 'candidate-manifest.json').write_bytes(canonical_bytes(candidate))
    plan = {'pairs_per_workload': PAIRS, 'workloads': WORKLOADS, 'warmup_seconds': WARMUP,
            'pilot_only': args.pilot,
            'environment_retries_per_pair': ENVIRONMENT_RETRIES,
            'client_window_seconds': WINDOW, 'client_duration_seconds': CLIENT_DURATION,
            'chunky_center_blocks': [CENTER, CENTER], 'chunky_radius_blocks': RADIUS,
            'control_qualification_id': qualification_id(manifests['without_C2ME']),
            'candidate_qualification_id': qualification_id(candidate),
            'correctness_source_sha': accepted['git_sha'], 'correctness_bundle_sha256': sha256(args.correctness_bundle)}
    (output / 'plan.json').write_bytes(canonical_bytes(plan))
    (output / 'plan.json').chmod(0o444)
    results = []
    decision = None
    phase = 'C2ME_PILOT' if args.pilot else 'C2ME_AB'
    save(output / 'progress.json', {'phase': phase, 'result': 'PENDING', 'recovery_status': 'PENDING'})
    try:
        maintenance.enter(output)
        if args.pilot:
            row = run_one(candidate, trial_directory(output, 'contention', 0, 0, 'C2ME_4'), 'contention', 'C2ME_4')
            results.append(row)
            save(output / 'results.json', results)
            decision = pilot_decision(row)
            save(output / 'analysis.json', decision)
            return decision
        for workload in WORKLOADS:
            for pair in range(PAIRS):
                def execute_run(workload, pair, attempt, variant):
                    if command('git', '-c', 'safe.directory=' + str(HERE.parent.parent), '-C', str(HERE.parent.parent),
                               'ls-remote', 'origin', 'refs/heads/work/minecraft-performance-manual').split()[0] != candidate['git_sha']:
                        raise RuntimeError('remote source moved during benchmark')
                    run_output = trial_directory(output, workload, pair, attempt, variant)
                    return run_one(manifests[variant], run_output, workload, variant)
                rejection = collect_trial_pair(workload, pair, execute_run, results)
                save(output / 'results.json', results)
                save(output / 'progress.json', {'phase': phase, 'result': 'PENDING',
                    'recovery_status': 'PENDING', 'completed_runs': len(results), 'workload': workload,
                    'completed_pair': pair + 1 if rejection is None else pair})
                if rejection is not None:
                    decision = {'result': 'INCONCLUSIVE', 'decision': None, 'rule': rejection,
                                'completed_runs': len(results)}
                    save(output / 'analysis.json', decision)
                    return decision
        decision = decide(results)
        save(output / 'analysis.json', decision)
        return decision
    except RunFailure as exc:
        results.append(exc.receipt)
        save(output / 'results.json', results)
        decision = {'result': 'FAIL' if exc.receipt['correctness'] == 'FAIL' else 'INCONCLUSIVE',
                    'decision': None, 'rule': exc.receipt['invalid_reason'],
                    'failed_run': exc.receipt['run_id'], 'completed_runs': len(results)}
        save(output / 'analysis.json', decision)
        return decision
    except BaseException:
        decision = {'result': 'INCONCLUSIVE', 'decision': None,
                    'rule': 'controller_or_runtime_failure', 'completed_runs': len(results)}
        save(output / 'analysis.json', decision)
        raise
    finally:
        maintenance.restore(output)
        maintenance.disarm()
        save(output / 'progress.json', {'phase': phase, 'result': decision['result'] if decision else 'INCONCLUSIVE',
                                      'recovery_status': 'PASS', 'completed_runs': len(results)})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('control-manifest', 'candidate-manifest', 'correctness-manifest', 'correctness-bundle', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--pilot', action='store_true', help='one calibration trial; never counts as A/B acceptance')
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('root required')
    def interrupted(*_):
        raise BenchmarkInterrupted('benchmark interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    result = execute(args)
    print(json.dumps(result))
    raise SystemExit({'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}[result['result']])
