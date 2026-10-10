"""Spec-driven physical zstd experiment. Evidence stays private by default."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

import runtime
from paired_statistics import balanced_order, sample_count, summarize


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def parse_output(text):
    matches = re.findall(r',\s*([0-9.]+) MB/s,\s*([0-9.]+) MB/s', text)
    if not matches:
        raise ValueError('zstd throughput record missing')
    values = dict(zip(('compression', 'decompression'), map(float, matches[-1])))
    if any(not math.isfinite(x) or x <= 0 for x in values.values()):
        raise ValueError('invalid zstd throughput')
    return values


def command(argv, **kwargs):
    return subprocess.run(argv, check=True, text=True, capture_output=True, **kwargs).stdout.strip()


def run(spec_path, build_path, output, repository):
    os.umask(0o077)
    output.mkdir(mode=0o700)  # Refuse to overwrite earlier evidence.
    (output / 'raw').mkdir()
    spec = json.loads(spec_path.read_text())
    build = json.loads(build_path.read_text())
    timers = ['nix-gc.timer', 'btrfs-scrub--.timer', 'fstrim.timer']
    stopped = []
    status = 'failed'
    def save(name, value):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    def snapshot():
        value = runtime.capture()
        runtime.validate_control(value, build['workingStock']['normal'], spec['physicalTarget'])
        return value
    try:
        if spec['schemaVersion'] != 2 or build['schemaVersion'] != 1:
            raise ValueError('unsupported artifact version')
        if build['source']['dirty'] or command(['git', '-C', str(repository), 'status', '--porcelain']):
            raise ValueError('measurement requires clean source')
        revision = command(['git', '-C', str(repository), 'rev-parse', 'HEAD'])
        if revision != build['source']['revision']:
            raise ValueError('source/build revision mismatch')
        build['source']['tree'] = command(['git', '-C', str(repository), 'rev-parse', 'HEAD^{tree}'])
        if digest(repository / 'flake.lock') != build['source']['lockSha256']:
            raise ValueError('source/build lock mismatch')
        if build['evaluatedSystem']['output'] != build['workingStock']['normal']:
            raise ValueError('evaluated system differs from stock control')
        if build['stage'] != spec['stage']:
            raise ValueError('spec/build stage mismatch')
        targets = {x['id']: x for x in spec['targets']}
        if set(targets) != {'stock', 'candidate'} or any(x['kind'] != 'package' for x in targets.values()):
            raise ValueError('zstd runner supports exactly stock/candidate package targets')
        binaries = {key: Path(value['output']) / 'bin/zstd' for key, value in build['packages'].items()}
        corpus = Path(build['workloadCorpus']['output']) / 'silesia'
        build['measuredInputs'] = {'binaries': {key: {'path': str(path), 'sha256': digest(path)} for key, path in binaries.items()},
                                   'corpus': {'path': str(corpus), 'sha256': digest(corpus), 'bytes': corpus.stat().st_size}}
        save('specification.json', spec)
        save('build.json', build)
        before = snapshot()
        save('runtime-before.json', before)
        for timer in timers:
            observed = subprocess.run(['systemctl', 'is-active', timer], text=True, capture_output=True)
            state = observed.stdout.strip()
            if state not in ('active', 'inactive'):
                raise ValueError(f'timer state unavailable: {timer}')
            if state == 'active':
                command(['sudo', '-n', 'systemctl', 'stop', timer])
                stopped.append(timer)
        snapshot()  # Check for maintenance activated during timer handling.
        observations = []
        summaries = {}
        for workload in spec['workloads']:
            if workload['command'][0] != 'zstd' or workload['corpusAttribute'] != 'silesia-corpus':
                raise ValueError('unsupported command/corpus contract')
            if set(x['id'] for x in workload['metrics']) != {'compression', 'decompression'}:
                raise ValueError('unsupported metric contract')
            def measure(variant, phase, pair, position):
                start = snapshot()
                name = f"{workload['id']}-{phase}-{pair}-{position}-{variant}"
                argv = ['taskset', '-c', str(workload['cpu']), str(binaries[variant]),
                        *workload['command'][1:], f"-i{workload['minimumSeconds']}", str(corpus)]
                started = now()
                result = subprocess.run(argv, text=True, capture_output=True,
                                        env={**os.environ, 'LC_ALL': 'C'}, timeout=120)
                (output / 'raw' / (name + '.txt')).write_text(result.stdout + result.stderr)
                end = snapshot()
                save('raw/' + name + '-runtime.json', {'before': start, 'after': end})
                runtime.validate_interval(start, end)
                if result.returncode:
                    raise ValueError('zstd command failed; raw output retained')
                record = {'workload': workload['id'], 'phase': phase, 'pair': pair,
                          'position': position, 'variant': variant, 'startedAt': started,
                          'finishedAt': now(), 'argv': argv, 'metrics': parse_output(result.stdout + result.stderr)}
                observations.append(record)
                with (output / 'observations.jsonl').open('a') as stream:
                    stream.write(json.dumps(record, sort_keys=True) + '\n')
                return record['metrics']
            for index in range(workload['warmupRuns']):
                for position, variant in enumerate(('stock', 'candidate')):
                    measure(variant, 'warmup', index, position)
            sampling = workload['sampling']
            def pairs(phase, count, seed):
                result = {metric['id']: [] for metric in workload['metrics']}
                for index, order in enumerate(balanced_order(count, seed)):
                    values = {}
                    for position, variant in enumerate(order):
                        variant = 'stock' if variant == 'control' else variant
                        values[variant] = measure(variant, phase, index, position)
                    for metric in result:
                        result[metric].append((values['stock'][metric], values['candidate'][metric]))
                return result
            pilot = pairs('pilot', sampling['pilotPairs'], sampling['orderSeed'])
            count = max(sample_count(pilot[m['id']], m['direction'], sampling['relativePrecision'],
                                     sampling['minimumPairs'], sampling['maximumPairs']) for m in workload['metrics'])
            measured = pairs('measurement', count, sampling['orderSeed'] + 1)
            summaries[workload['id']] = {'pilotPairs': sampling['pilotPairs'], 'measurementPairs': count,
                'metrics': {m['id']: summarize(measured[m['id']], m['direction'], sampling['effectThreshold'],
                                              sampling['orderSeed']) for m in workload['metrics']}}
        after = snapshot()
        save('runtime-after.json', after)
        runtime.validate_interval(before, after)
        save('results.json', {'schemaVersion': 1, 'kind': 'nixos-experiment-results',
                             'finishedAt': now(), 'summaries': summaries, 'observations': observations})
        status = 'complete'
    finally:
        for timer in stopped:
            command(['sudo', '-n', 'systemctl', 'start', timer])
        files = {str(path.relative_to(output)): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
        save('artifact-index.json', {'schemaVersion': 1, 'kind': 'nixos-experiment-artifact-index',
                                    'status': status, 'finishedAt': now(), 'sha256': files})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('specification', 'build', 'output', 'repository'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        run(args.specification, args.build, args.output, args.repository)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'Experiment refused or failed: {error}', file=sys.stderr)
        sys.exit(1)
