"""Paired, disposable DH idle attribution; never activates production configuration."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from idle_metrics import pair_valid, summarize, unique_java, validate_rapl
from qualification_manifest import canonical_bytes, controlled_path, qualification_id, sha256, validate_candidate
from generate_candidate_manifest import baseline_identity
from analyze_dh_idle import analyze
import maintenance

JAVA = WRAPPER = MODS = BASE = CANDIDATE = None
OUTPUT = None
UNIT = 'minecraft-performance-attribution.service'
RAPL = Path('/sys/class/powercap/intel-rapl:0')
HERE = Path(__file__).resolve().parent


def command(*args):
    return subprocess.check_output(args, text=True)


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.chmod(0o600)
    temp.replace(path)


def counters(path):
    return dict((k, int(v)) for k, v in (line.split() for line in path.read_text().splitlines()))


def file_sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def disk_state(world):
    # Include content hashes: fixed-size SQLite and region mutations matter too.
    result = {}
    for p in sorted(world.rglob('*')):
        # SQLite's -shm is a reconstructible WAL index, not database content.
        # Its physical I/O is still included in the cgroup I/O gate.
        if p.is_file() and (p.suffix in ('.mca', '.sqlite') or p.name.endswith('-wal')):
            with p.open('rb') as stream:
                result[str(p.relative_to(world))] = {
                    'size': p.stat().st_size, 'sha256': hashlib.file_digest(stream, 'sha256').hexdigest()}
    return result


def threads(pid):
    result = {}
    for task in Path(f'/proc/{pid}/task').iterdir():
        try:
            fields = (task / 'stat').read_text().rsplit(') ', 1)[1].split()
            result[task.name] = {'name': (task / 'comm').read_text().strip(),
                                 'ticks': int(fields[11]) + int(fields[12])}
        except (FileNotFoundError, ProcessLookupError):
            continue
    return result


def collect_sample(cg, rapl, mode, pid, host_stat=Path('/proc/stat')):
    if mode not in ('clean', 'diagnostic'):
        raise ValueError('unknown measurement mode')
    row = {'time': time.monotonic(), 'utc': time.time(),
           'cpu': counters(cg / 'cpu.stat'), 'memory_events': counters(cg / 'memory.events'),
           'memory': int((cg / 'memory.current').read_text()), 'io': (cg / 'io.stat').read_text(),
           'energy_uj': int((rapl / 'energy_uj').read_text()),
           'host_cpu': host_stat.read_text().splitlines()[0]}
    if mode == 'diagnostic':
        row['threads'] = threads(pid)
        row['logical_cpu_idle_residency_us'] = idle_residency()
    return row


def idle_residency():
    return {str(p): p.read_text().strip()
            for p in Path('/sys/devices/system/cpu').glob('cpu*/cpuidle/state*/time')}


def minecraft_clients():
    """Detect conflicting clients using paths only; never read authentication arguments."""
    found = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if (process / 'comm').read_text().strip() != 'java':
                continue
            cwd = str((process / 'cwd').resolve())
            if '/PrismLauncher/instances/' in cwd or '/minecraft-performance-client-' in cwd:
                found.append(int(process.name))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return found


def wait_quiet(output):
    # Bounded environmental retries; do not stop unrelated applications.
    for attempt in range(1, 4):
        deadline = time.monotonic() + 300
        quiet_since = None
        while time.monotonic() < deadline:
            clients = minecraft_clients()
            save(output / 'quiet-window.json', {'attempt': attempt, 'conflicting_client_pids': clients,
                                                'quiet_since': quiet_since, 'deadline': deadline})
            if clients:
                quiet_since = None
            elif quiet_since is None:
                quiet_since = time.monotonic()
            elif time.monotonic() - quiet_since >= 60:
                return
            time.sleep(5)
    raise RuntimeError('INCONCLUSIVE_ENVIRONMENT_NOISE: normal Minecraft client still active after three bounded waits')


def prepare(output, name, run_name):
    if baseline_identity(BASE) != CANDIDATE['baseline']:
        raise RuntimeError('baseline identity or immutable content changed')
    root = controlled_path(output / run_name, output)
    subprocess.run(['btrfs', 'subvolume', 'snapshot', str(BASE), str(root)], check=True)
    server = root / 'survival'
    # Replace inherited managed links only inside this new snapshot.
    for filename in ('mods', 'server.properties', 'eula.txt'):
        p = server / filename
        if p.is_symlink() or p.is_file():
            p.unlink()
    (server / 'mods').mkdir()
    for mod in MODS.iterdir():
        if name.endswith('off') and mod.name.startswith('DistantHorizons'):
            continue
        (server / 'mods' / mod.name).symlink_to(mod)
    (server / 'eula.txt').write_text('eula=true\n')
    properties = CANDIDATE['controlled_server_properties']
    (server / 'server.properties').write_text(''.join(
        f'{key}={str(value).lower() if isinstance(value, bool) else value}\n'
        for key, value in sorted(properties.items())))
    for filename, policy in CANDIDATE['policies'].items():
        target = server / filename
        if target.parent != target.parent.resolve() or not target.parent.is_relative_to(server):
            raise RuntimeError('policy parent escapes disposable server')
        if target.is_symlink():
            target.unlink()
        target.write_text(policy['content'])
    realtime = 'false' if name in ('diagnostic-realtime', 'diagnostic-all') else 'true'
    sync = 'false' if name in ('diagnostic-sync', 'diagnostic-all') else 'true'
    plan = 'DISABLED' if name in ('diagnostic-generation', 'diagnostic-all') else 'CHUNKS_ONLY'
    if name.startswith('diagnostic'):
        (server / 'config' / 'DistantHorizons.toml').write_text(
        '_version = 5\n[server]\nsynchronizeOnLoad = ' + sync + '\n'
        'enableRealTimeUpdates = ' + realtime + '\n'
        'sendLevelKeys = ' + ('false' if name == 'diagnostic-all' else 'true') + '\n'
        '[common.worldGenerator]\nchunkGeneratorMode = "PRE_EXISTING_ONLY"\n'
        'generatorPlan = "' + plan + '"\n[common.multiThreading]\n'
        'numberOfThreads = 2\nthreadRunTimeRatio = "0.5"\n')
    subprocess.run(['chown', '-R', 'minecraft:minecraft', str(root)], check=True)
    return root, server


def run(output, name, duration, attempt=0):
    maintenance.refresh()
    mode = 'diagnostic' if name.startswith('diagnostic') else 'clean'
    wait_quiet(output)
    run_name = name if not attempt else name + f'-retry-{attempt}'
    evidence = output / (run_name + '-evidence')
    evidence.mkdir(mode=0o700)
    root, server = prepare(output, name, run_name)
    log = evidence / 'server.log'
    log.touch(mode=0o600)
    subprocess.run(['systemd-run', '--unit=' + UNIT, '--collect',
        '--property=User=minecraft', '--property=Group=minecraft',
        '--property=WorkingDirectory=' + str(server), '--property=Nice=' + str(CANDIDATE['service']['Nice']),
        '--property=Slice=minecraftperformance.slice',
        '--property=MemoryHigh=' + CANDIDATE['service']['MemoryHigh'],
        '--property=MemoryMax=' + CANDIDATE['service']['MemoryMax'],
        '--property=RuntimeMaxSec=1200',
        '--property=KillMode=mixed', '--property=TimeoutStopSec=120',
        '--property=StandardOutput=append:' + str(log),
        '--property=StandardError=append:' + str(log),
        sys.executable, str(HERE / 'server_runner.py'),
        '--console', str(root / 'console.sock'), WRAPPER,
        *CANDIDATE['jvm_flags']], check=True)
    try:
        deadline = time.monotonic() + 240
        while not log.exists() or 'pausing' not in log.read_text().lower():
            if time.monotonic() > deadline or command('systemctl', 'is-active', UNIT).strip() != 'active':
                raise RuntimeError('server did not enter normal empty pause')
            time.sleep(2)
        # Hashing itself causes disk and CPU activity: settle after this work.
        before_world = disk_state(server / 'world')
        time.sleep(90)
        group = command('systemctl', 'show', UNIT, '-p', 'ControlGroup', '--value').strip()
        cg = Path('/sys/fs/cgroup') / group.lstrip('/')
        pids = []
        for p in Path('/proc').iterdir():
            if not p.name.isdigit():
                continue
            try:
                if any(line.endswith(':' + group) for line in (p / 'cgroup').read_text().splitlines()) and \
                        (p / 'cmdline').read_bytes().split(b'\0')[0].endswith(b'/bin/java'):
                    pids.append(int(p.name))
            except (FileNotFoundError, ProcessLookupError):
                pass
        pid = unique_java(pids)
        if not group.startswith('/minecraftperformance.slice/'):
            raise RuntimeError('benchmark not inside equivalent top-level slice')
        if mode == 'diagnostic':
            (evidence / 'threads-before.txt').write_text(command(str(JAVA / 'jcmd'), str(pid), 'Thread.print', '-l'))
            command(str(JAVA / 'jcmd'), str(pid), 'JFR.start', 'name=idle',
                    'settings=' + str(output / 'idle.jfc'), 'disk=false')
        max_energy = int((RAPL / 'max_energy_range_uj').read_text())
        clients_before = minecraft_clients()
        time.sleep(10)
        save(evidence / 'measurement.json', {'mode': mode, 'start_monotonic': time.monotonic(),
                                             'duration': duration})

        def sample():
            return collect_sample(cg, RAPL, mode, pid)

        rows = [sample()]
        for i in range(duration):
            time.sleep(max(0, rows[0]['time'] + i + 1 - time.monotonic()))
            rows.append(sample())
        # Persistent output, JFR dumping and fingerprints happen after the interval.
        with (evidence / 'samples.jsonl').open('w') as stream:
            for row in rows:
                stream.write(json.dumps(row) + '\n')
        elapsed = rows[-1]['time'] - rows[0]['time']
        thread_cpu = {}
        hz = os.sysconf('SC_CLK_TCK')
        for a, b in zip(rows, rows[1:]):
            for tid, value in b.get('threads', {}).items():
                if tid in a.get('threads', {}):
                    entry = thread_cpu.setdefault(tid, {'name': value['name'], 'cpu_seconds': 0})
                    entry['cpu_seconds'] += (value['ticks'] - a['threads'][tid]['ticks']) / hz
        for entry in thread_cpu.values():
            entry['one_core_pct'] = entry['cpu_seconds'] / elapsed * 100
        after_world = disk_state(server / 'world')
        result = {'variant': name, 'mode': mode, 'pid': pid, 'attempt': attempt,
                  'evidence': str(evidence),
                  **summarize(rows, max_energy, os.cpu_count()),
                  'environment_clients_absent': not clients_before and not minecraft_clients(),
                  'world_unchanged': before_world == after_world,
                  'io_before': rows[0]['io'], 'io_after': rows[-1]['io'],
                  'threads': sorted(thread_cpu.items(), key=lambda x: -x[1]['cpu_seconds'])}
        save(evidence / 'world-before.json', before_world)
        save(evidence / 'world-after.json', after_world)
        save(evidence / 'result.json', result)
        if mode == 'diagnostic':
            command(str(JAVA / 'jcmd'), str(pid), 'JFR.stop', 'name=idle',
                    'filename=' + str(root / 'idle.jfr'))
            shutil.copy2(root / 'idle.jfr', evidence / 'idle.jfr')
            (evidence / 'threads-after.txt').write_text(command(str(JAVA / 'jcmd'), str(pid), 'Thread.print', '-l'))
            with (evidence / 'jfr-events.json').open('w') as stream:
                subprocess.run([str(JAVA / 'jfr'), 'print', '--json', '--events',
                                'jdk.ExecutionSample,jdk.NativeMethodSample,jdk.ThreadCPULoad,jdk.CPULoad',
                                str(evidence / 'idle.jfr')], stdout=stream, check=True)
        return result
    finally:
        subprocess.run(['systemctl', 'stop', UNIT], check=False)


def execute_main():
    global JAVA, WRAPPER, MODS, BASE, CANDIDATE, OUTPUT
    os.environ['PATH'] = '/run/current-system/sw/bin:/nix/store/833invqvsk7anqnqrki5hqncrcllj825-coreutils-9.11/bin'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    CANDIDATE = json.loads(args.manifest.read_text())
    validate_candidate(CANDIDATE, HERE.parent.parent)
    if CANDIDATE.get('schema') != 1:
        parser.error('unsupported candidate manifest schema')
    if (CANDIDATE['service']['CPUWeight'], CANDIDATE['service']['IOWeight']) != (50, 50):
        parser.error('disposable slice definition must match frozen candidate weights')
    if args.manifest.read_bytes() != canonical_bytes(CANDIDATE):
        parser.error('manifest must have canonical immutable encoding')
    JAVA = Path(CANDIDATE['diagnostic_java_home']) / 'bin'
    WRAPPER = CANDIDATE['wrapper']['path']
    MODS = Path(CANDIDATE['mods_directory'])
    BASE = Path(CANDIDATE['baseline']['path'])
    for artifact in [CANDIDATE['wrapper'], CANDIDATE['java'], *CANDIDATE['mods'], *CANDIDATE['policies'].values()]:
        if sha256(artifact['path']) != artifact['sha256']:
            parser.error('candidate artifact hash mismatch')
    for filename, digest in CANDIDATE['tool_source_files'].items():
        path = Path(filename)
        if path.is_absolute() or '..' in path.parts or sha256(HERE.parent.parent / path) != digest:
            parser.error('qualification source differs from frozen candidate')
    for policy in CANDIDATE['policies'].values():
        if hashlib.sha256(policy['content'].encode()).hexdigest() != policy['sha256']:
            parser.error('candidate policy content differs from immutable artifact')
    controlled_path(args.output, Path('/persist'))
    if args.output.parent != Path('/persist') or not args.output.name.startswith('minecraft-performance-dh-attribution-'):
        parser.error('output must be a new direct private attribution directory under /persist')
    if os.geteuid() != 0 or args.output.exists() or not args.output.is_relative_to(Path('/persist')):
        parser.error('requires root and a new private persistent output directory')
    os.umask(0o077)
    args.output.mkdir(mode=0o710)
    args.output.chmod(0o710)
    OUTPUT = args.output
    (args.output / 'candidate-manifest.json').write_bytes(canonical_bytes(CANDIDATE))
    (args.output / 'candidate-manifest.json').chmod(0o444)
    subprocess.run(['chown', 'root:minecraft', str(args.output)], check=True)
    maximum = int((RAPL / 'max_energy_range_uj').read_text())
    validate_rapl((RAPL / 'name').read_text().strip(), int((RAPL / 'enabled').read_text()), maximum)
    int((RAPL / 'energy_uj').read_text())
    if command('systemctl', 'show', UNIT, '-p', 'LoadState', '--value').strip() != 'not-found':
        raise RuntimeError('refuse occupied disposable server unit name')
    slice_path = Path('/run/systemd/system/minecraftperformance.slice')
    if slice_path.exists() and (slice_path.is_symlink() or slice_path.read_text() != maintenance.SLICE_TEXT):
        raise RuntimeError('refuse overwrite of unrelated slice unit')
    maintenance.enter(args.output)
    # Hyphens imply nested slices, so this spelling deliberately has no hyphen.
    slice_path.write_text(maintenance.SLICE_TEXT)
    subprocess.run(['systemctl', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', 'start', 'minecraftperformance.slice'], check=True)
    save(args.output / 'receipt.json', {'rapl_path': str(RAPL.resolve()), 'rapl_name': 'package-0',
         'qualification_id': qualification_id(CANDIDATE),
         'rapl_enabled': 1, 'rapl_max_energy_range_uj': maximum, 'base': str(BASE),
         'base_subvolume': command('btrfs', 'subvolume', 'show', str(BASE)),
         'branch_sha': command('git', '-c', 'safe.directory=' + str(HERE.parent.parent),
                                '-C', str(HERE), 'rev-parse', 'HEAD').strip(),
         'production_system': str(Path('/run/current-system').resolve()),
         'wrapper_sha256': hashlib.sha256(Path(WRAPPER).read_bytes()).hexdigest(),
         'helper_sha256': hashlib.sha256((HERE / 'idle_metrics.py').read_bytes()).hexdigest(),
         'mod_sha256': {p.name: file_sha256(p) for p in MODS.iterdir()},
         'slice': command('systemctl', 'show', 'minecraftperformance.slice',
                          '-p', 'ControlGroup', '-p', 'CPUWeight', '-p', 'IOWeight'),
         'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    save(args.output / 'sampling-plan.json', {'fixed_valid_pairs': 11,
         'interim_inferential_looks': 0, 'primary_estimand': 'mean paired package-power delta',
         'order': 'alternating off/on and on/off', 'maximum_environment_retries_per_pair': 3,
         'measurement_seconds_per_run': 600})
    subprocess.run([str(JAVA / 'jfr'), 'configure', '--input', 'none',
                    '+jdk.ExecutionSample#enabled=true', '+jdk.ExecutionSample#period=20ms',
                    '+jdk.NativeMethodSample#enabled=true', '+jdk.NativeMethodSample#period=20ms',
                    '+jdk.ThreadCPULoad#enabled=true', '+jdk.ThreadCPULoad#period=1s',
                    '+jdk.CPULoad#enabled=true', '+jdk.CPULoad#period=1s',
                    '--output', str(args.output / 'idle.jfc')], check=True)
    (args.output / 'idle.jfc').chmod(0o644)
    results = []
    rejected = []

    def execute(variant, attempt=0):
        name = variant if not attempt else variant + f'-retry-{attempt}'
        save(args.output / 'progress.json', {'phase': 'DH_IDLE_ATTRIBUTION', 'running': name,
                                            'completed': [r['variant'] for r in results]})
        result = run(args.output, variant, 600, attempt)
        if any(result['memory_events_delta'].values()):
            raise RuntimeError('FAIL_MEMORY_PRESSURE: memory event gate failed')
        if not result['world_unchanged']:
            raise RuntimeError('FAIL_BACKGROUND_WORLD_DATABASE_MUTATION')
        return result

    for i in range(1, 12):
        for attempt in range(4):
            order = ('off', 'on') if i % 2 else ('on', 'off')
            measured = {v: execute(f'pair-{i}-{v}', attempt) for v in order}
            if pair_valid(measured['off'], measured['on']):
                results.extend(measured[v] for v in order)
                save(args.output / 'results.json', results)
                break
            rejected.append({'pair': i, 'retry': attempt, 'result': 'INCONCLUSIVE',
                             'reason': 'ENVIRONMENT_CONFOUND', 'runs': measured})
            save(args.output / 'rejected-pairs.json', rejected)
        else:
            raise RuntimeError('INCONCLUSIVE_ENVIRONMENT_NOISE: three paired retries exhausted')
    decision = analyze(args.output)
    save(args.output / 'analysis.json', decision)
    # Profiling is justified only by a definitive clean resource failure.
    resource_failure = (decision['median_on_interval_cpu_pct'] > 5
                        or decision['median_on_p95_cpu_pct'] > 10
                        or decision['power_acceptance'] == 'FAIL')
    if decision['idle_acceptance'] == 'FAIL' and resource_failure:
        for variant in ('diagnostic-off', 'diagnostic-normal', 'diagnostic-realtime',
                        'diagnostic-sync', 'diagnostic-generation', 'diagnostic-all'):
            results.append(execute(variant))
            save(args.output / 'results.json', results)
    save(args.output / 'progress.json', {'phase': 'DH_IDLE_ATTRIBUTION', 'result': 'INCONCLUSIVE',
                                        'reason': 'MEASUREMENTS_COMPLETE_AWAITING_ADJUDICATION',
                                        'completed': [r['variant'] for r in results]})


if __name__ == '__main__':
    def terminate(signum, frame):
        raise SystemExit('qualification interrupted by signal ' + str(signum))
    signal.signal(signal.SIGTERM, terminate)
    try:
        execute_main()
    finally:
        if OUTPUT is not None and (OUTPUT / 'maintenance.json').exists():
            maintenance.restore(OUTPUT)
            if (OUTPUT / 'guard-armed').exists():
                maintenance.disarm()
