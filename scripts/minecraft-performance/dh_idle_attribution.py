"""Paired, disposable DH idle attribution; never activates production configuration."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time

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


def disk_state(world):
    # Include content hashes: fixed-size SQLite and region mutations matter too.
    return {str(p.relative_to(world)): {'size': p.stat().st_size,
            'sha256': hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()}
            for p in sorted(world.rglob('*')) if p.is_file() and
            (p.suffix in ('.mca', '.sqlite') or p.name.endswith(('-wal', '-shm')))}


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


def prepare(output, name):
    root = output / name
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


def run(output, name, duration):
    evidence = output / (name + '-evidence')
    evidence.mkdir(mode=0o700)
    root, server = prepare(output, name)
    log = evidence / 'server.log'
    log.touch(mode=0o600)
    subprocess.run(['systemd-run', '--unit=' + UNIT, '--collect',
        '--property=User=minecraft', '--property=Group=minecraft',
        '--property=WorkingDirectory=' + str(server), '--property=Nice=5',
        '--property=CPUWeight=50', '--property=IOWeight=50',
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
        if len(pids) != 1:
            raise RuntimeError('expected exactly one fresh Java process')
        pid = pids[0]
        command(str(JAVA / 'jcmd'), str(pid), 'Thread.print', '-l')
        (evidence / 'threads-before.txt').write_text(command(str(JAVA / 'jcmd'), str(pid), 'Thread.print', '-l'))
        # JFR startup/attach work happens before the measured interval.
        command(str(JAVA / 'jcmd'), str(pid), 'JFR.start', 'name=idle',
                'settings=' + str(output / 'idle.jfc'), 'disk=false')
        time.sleep(10)
        before_world = disk_state(server / 'world')
        max_energy = int((RAPL / 'max_energy_range_uj').read_text())

        def sample():
            return {'time': time.monotonic(), 'utc': time.time(),
                    'cpu_ns': int(command('systemctl', 'show', UNIT, '-p', 'CPUUsageNSec', '--value')),
                    'cpu': counters(cg / 'cpu.stat'), 'memory_events': counters(cg / 'memory.events'),
                    'memory': int((cg / 'memory.current').read_text()),
                    'io': (cg / 'io.stat').read_text(), 'threads': threads(pid),
                    'energy_uj': int((RAPL / 'energy_uj').read_text()),
                    'host_cpu': Path('/proc/stat').read_text().splitlines()[0],
                    'logical_cpu_idle_residency_us': {str(p): p.read_text().strip()
                        for p in Path('/sys/devices/system/cpu').glob('cpu*/cpuidle/state*/time')}}

        rows = [sample()]
        with (evidence / 'samples.jsonl').open('w') as stream:
            stream.write(json.dumps(rows[0]) + '\n')
            for i in range(duration):
                time.sleep(max(0, rows[0]['time'] + i + 1 - time.monotonic()))
                rows.append(sample())
                stream.write(json.dumps(rows[-1]) + '\n')
                stream.flush()
        elapsed = rows[-1]['time'] - rows[0]['time']
        energy = sum((b['energy_uj'] - a['energy_uj']) % max_energy for a, b in zip(rows, rows[1:]))
        cpu = [(b['cpu_ns'] - a['cpu_ns']) / (b['time'] - a['time']) / 1e7
               for a, b in zip(rows, rows[1:])]
        thread_cpu = {}
        hz = os.sysconf('SC_CLK_TCK')
        for a, b in zip(rows, rows[1:]):
            for tid, value in b['threads'].items():
                if tid in a['threads']:
                    entry = thread_cpu.setdefault(tid, {'name': value['name'], 'cpu_seconds': 0})
                    entry['cpu_seconds'] += (value['ticks'] - a['threads'][tid]['ticks']) / hz
        for entry in thread_cpu.values():
            entry['one_core_pct'] = entry['cpu_seconds'] / elapsed * 100
        after_world = disk_state(server / 'world')
        result = {'variant': name, 'pid': pid, 'duration': elapsed,
                  'service_cpu_median_one_core_pct': statistics.median(cpu),
                  'service_cpu_interval_one_core_pct': (rows[-1]['cpu_ns'] - rows[0]['cpu_ns']) / elapsed / 1e7,
                  'package_power_w': energy / 1e6 / elapsed,
                  'package_energy_j': energy / 1e6,
                  'memory_events_delta': {k: rows[-1]['memory_events'][k] - v
                      for k, v in rows[0]['memory_events'].items()},
                  'world_unchanged': before_world == after_world,
                  'io_before': rows[0]['io'], 'io_after': rows[-1]['io'],
                  'threads': sorted(thread_cpu.items(), key=lambda x: -x[1]['cpu_seconds'])}
        save(evidence / 'world-before.json', before_world)
        save(evidence / 'world-after.json', after_world)
        save(evidence / 'result.json', result)
        command(str(JAVA / 'jcmd'), str(pid), 'JFR.stop', 'name=idle',
                'filename=' + str(root / 'idle.jfr'))
        shutil.copy2(root / 'idle.jfr', evidence / 'idle.jfr')
        (evidence / 'threads-after.txt').write_text(command(str(JAVA / 'jcmd'), str(pid), 'Thread.print', '-l'))
        # Convert JFR only after the fixed CPU/energy interval is over.
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
    subprocess.run([str(JAVA / 'jfr'), 'configure', '--input', 'none',
                    '+jdk.ExecutionSample#enabled=true', '+jdk.ExecutionSample#period=20ms',
                    '+jdk.NativeMethodSample#enabled=true', '+jdk.NativeMethodSample#period=20ms',
                    '+jdk.ThreadCPULoad#enabled=true', '+jdk.ThreadCPULoad#period=1s',
                    '+jdk.CPULoad#enabled=true', '+jdk.CPULoad#period=1s',
                    '--output', str(args.output / 'idle.jfc')], check=True)
    (args.output / 'idle.jfc').chmod(0o644)
    results = []
    variants = [f'pair-{i}-{v}' for i in range(1, 6)
                for v in (('off', 'on') if i % 2 else ('on', 'off'))]
    variants += ['diagnostic-realtime', 'diagnostic-sync', 'diagnostic-generation', 'diagnostic-all']
    for variant in variants:
        save(args.output / 'progress.json', {'phase': 'DH_IDLE_ATTRIBUTION', 'running': variant,
                                            'completed': [r['variant'] for r in results]})
        result = run(args.output, variant, 600)
        results.append(result)
        save(args.output / 'results.json', results)
        if any(result['memory_events_delta'][k] for k in ('max', 'oom', 'oom_kill')):
            raise RuntimeError('memory correctness gate failed')
    save(args.output / 'progress.json', {'phase': 'DH_IDLE_ATTRIBUTION', 'result': 'MEASURED',
                                        'completed': [r['variant'] for r in results]})


if __name__ == '__main__':
    main()
