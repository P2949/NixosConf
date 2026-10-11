"""Paired, disposable DH idle attribution; never activates production configuration."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from idle_metrics import pair_valid, summarize, unique_java, validate_rapl

JAVA = Path('/nix/store/jzgzdbryqzji2a6wqcxmbw46hqm7bga5-openjdk-25.0.4.1+1/bin')
WRAPPER = '/nix/store/z3x5r4lcpr7x20nkpghfb4bcxyv2dhs4-minecraft-server/bin/minecraft-server'
MODS = Path('/nix/store/c88ym3hqq9axkhws6yrfnchv43n4y1wl-minecraft-survival-mods')
BASE = Path('/persist/minecraft-performance-lab-20261011-012354-832014a/base')
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
    root = output / run_name
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
    (server / 'server.properties').write_text(
        'server-ip=127.0.0.1\nserver-port=25576\nonline-mode=false\n'
        'enable-rcon=false\nmanagement-server-enabled=false\n'
        'pause-when-empty-seconds=60\nview-distance=12\nsimulation-distance=8\n'
        'level-name=world\nwhite-list=false\nmax-players=10\n')
    realtime = 'false' if name in ('diagnostic-realtime', 'diagnostic-all') else 'true'
    sync = 'false' if name in ('diagnostic-sync', 'diagnostic-all') else 'true'
    plan = 'DISABLED' if name in ('diagnostic-generation', 'diagnostic-all') else 'CHUNKS_ONLY'
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
        '--property=WorkingDirectory=' + str(server), '--property=Nice=5',
        '--property=Slice=minecraftperformance.slice',
        '--property=MemoryHigh=10G', '--property=MemoryMax=12G',
        '--property=RuntimeMaxSec=1200',
        '--property=KillMode=mixed', '--property=TimeoutStopSec=120',
        '--property=StandardOutput=append:' + str(log),
        '--property=StandardError=append:' + str(log),
        sys.executable, str(HERE / 'server_runner.py'),
        '--console', str(root / 'console.sock'), WRAPPER,
        '-Xms1G', '-Xmx8G', '-XX:+ExitOnOutOfMemoryError', '-XX:+UseG1GC'], check=True)
    try:
        deadline = time.monotonic() + 240
        while not log.exists() or 'pausing' not in log.read_text().lower():
            if time.monotonic() > deadline or command('systemctl', 'is-active', UNIT).strip() != 'active':
                raise RuntimeError('server did not enter normal empty pause')
            time.sleep(2)
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
        before_world = disk_state(server / 'world')
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


def main():
    os.environ['PATH'] = '/run/current-system/sw/bin:/nix/store/833invqvsk7anqnqrki5hqncrcllj825-coreutils-9.11/bin'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or args.output.exists() or not args.output.is_relative_to(Path('/persist')):
        parser.error('requires root and a new private persistent output directory')
    os.umask(0o077)
    args.output.mkdir(mode=0o710)
    args.output.chmod(0o710)
    subprocess.run(['chown', 'root:minecraft', str(args.output)], check=True)
    maximum = int((RAPL / 'max_energy_range_uj').read_text())
    validate_rapl((RAPL / 'name').read_text().strip(), int((RAPL / 'enabled').read_text()), maximum)
    int((RAPL / 'energy_uj').read_text())
    # Hyphens imply nested slices, so this spelling deliberately has no hyphen.
    slice_path = Path('/run/systemd/system/minecraftperformance.slice')
    slice_path.write_text('[Unit]\nDescription=Disposable Minecraft qualification slice\n'
                          '[Slice]\nCPUWeight=50\nIOWeight=50\n')
    subprocess.run(['systemctl', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', 'start', 'minecraftperformance.slice'], check=True)
    save(args.output / 'receipt.json', {'rapl_path': str(RAPL.resolve()), 'rapl_name': 'package-0',
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

    for i in range(1, 6):
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
    # Power acceptance is already complete before any profiler starts.
    for variant in ('diagnostic-off', 'diagnostic-normal', 'diagnostic-realtime',
                    'diagnostic-sync', 'diagnostic-generation', 'diagnostic-all'):
        results.append(execute(variant))
        save(args.output / 'results.json', results)
    save(args.output / 'progress.json', {'phase': 'DH_IDLE_ATTRIBUTION', 'result': 'INCONCLUSIVE',
                                        'reason': 'MEASUREMENTS_COMPLETE_AWAITING_ADJUDICATION',
                                        'completed': [r['variant'] for r in results]})


if __name__ == '__main__':
    main()
