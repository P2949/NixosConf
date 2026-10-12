"""Disposable candidate lifecycle for automated functional qualification."""

import importlib.util
from pathlib import Path
import socket
import subprocess
import sys
import time

from generate_candidate_manifest import baseline_identity
from qualification_manifest import controlled_path, sha256, validate_candidate
from idle_metrics import unique_java
import maintenance

HERE = Path(__file__).resolve().parent
UNIT = 'minecraft-performance-functional.service'


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def identity_helper():
    path = HERE.parent.parent / 'hosts/desktop/minecraft-dh-identity.py'
    spec = importlib.util.spec_from_file_location('candidate_dh_identity', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Lab:
    def __init__(self, manifest, output):
        validate_candidate(manifest, HERE.parent.parent)
        self.manifest = manifest
        self.output = controlled_path(output, Path('/persist'))
        if self.output.parent != Path('/persist') or not self.output.name.startswith('minecraft-performance-functional-'):
            raise ValueError('functional output must be a direct private namespace')
        if baseline_identity(Path(manifest['baseline']['path'])) != manifest['baseline']:
            raise ValueError('baseline changed before functional clone')
        self.output.mkdir(mode=0o710)
        self.output.chmod(0o710)
        subprocess.run(['chown', 'root:minecraft', str(self.output)], check=True)
        self.root = self.output / 'world-clone'
        subprocess.run(['btrfs', 'subvolume', 'snapshot', manifest['baseline']['path'], str(self.root)], check=True)
        self.server = controlled_path(self.root / 'survival', self.root, existing=True)
        self.console = self.root / 'console.sock'
        self.phase = 0
        self.active = False
        self.owns_slice = False

    def install(self, pregen=False):
        if self.active:
            raise RuntimeError('policy replacement requires stopped functional server')
        helper = identity_helper()
        policy = self.server / 'config/DistantHorizons.toml'
        identity = self.server / 'config/distant-horizons-server-id'
        if policy.parent != policy.parent.resolve() or identity.is_symlink():
            raise ValueError('identity/configuration parent alias prohibited')
        helper.capture(policy, identity)
        mods = self.server / 'mods'
        if mods.is_symlink():
            mods.unlink()
        elif mods.exists():
            for path in mods.iterdir():
                if not path.is_symlink() or not path.name.endswith('.jar'):
                    raise ValueError('unexpected functional mod directory entry')
                path.unlink()
            mods.rmdir()
        mods.mkdir()
        inventory = self.manifest['pregen_mods'] if pregen else self.manifest['mods']
        for mod in inventory:
            if sha256(mod['path']) != mod['sha256']:
                raise ValueError('functional mod artifact hash mismatch')
            (mods / mod['filename']).symlink_to(mod['path'])
        if probe := self.manifest.get('server_tick_probe'):
            if sha256(probe['path']) != probe['sha256']:
                raise ValueError('server tick probe artifact changed')
            (mods / 'server-tick-probe.jar').symlink_to(probe['path'])
        for filename, entry in self.manifest['policies'].items():
            destination = self.server / filename
            if destination.parent != destination.parent.resolve():
                raise ValueError('policy parent alias prohibited')
            if destination.is_symlink():
                destination.unlink()
            destination.write_text(entry['content'])
        if pregen:
            policy.write_text(self.manifest['pregen_policy']['content'])
        helper.apply(policy, identity)
        properties = dict(self.manifest['controlled_server_properties'])
        if pregen:
            properties['pause-when-empty-seconds'] = self.manifest['pregen_pause_seconds']
        for filename in ('server.properties', 'eula.txt'):
            path = self.server / filename
            if path.is_symlink():
                path.unlink()
        (self.server / 'server.properties').write_text(''.join(
            f'{key}={str(value).lower() if isinstance(value, bool) else value}\n'
            for key, value in sorted(properties.items())))
        (self.server / 'eula.txt').write_text('eula=true\n')
        subprocess.run(['chown', '-R', 'minecraft:minecraft', str(self.root)], check=True)

    def start(self, pregen=False):
        if command('systemctl', 'show', UNIT, '-p', 'LoadState', '--value') != 'not-found':
            raise RuntimeError('functional unit name occupied')
        slice_path = Path('/run/systemd/system') / maintenance.SLICE
        if slice_path.exists():
            raise RuntimeError('functional slice name occupied')
        self.install(pregen)
        slice_path.write_text(maintenance.SLICE_TEXT)
        self.owns_slice = True
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'start', maintenance.SLICE], check=True)
        self.phase += 1
        self.log = self.output / f'server-phase-{self.phase}.log'
        recording_args = []
        if self.manifest.get('server_tick_probe'):
            self.tick_output = self.output / f'server-phase-{self.phase}-ticks.csv'
            self.jfr_output = self.output / f'server-phase-{self.phase}.jfr'
            for path in (self.tick_output, self.jfr_output):
                with path.open('xb'):
                    pass
                path.chmod(0o660)
                subprocess.run(['chown', 'minecraft:minecraft', str(path)], check=True)
            recording_args = ['--setenv=MINECRAFT_TICK_OUTPUT=' + str(self.tick_output)]
        service = self.manifest['service']
        self.active = True
        subprocess.run(['systemd-run', '--collect', '--unit=' + UNIT,
            '--property=User=minecraft', '--property=Group=minecraft',
            '--property=WorkingDirectory=' + str(self.server), '--property=Slice=' + maintenance.SLICE,
            '--property=Nice=' + str(service['Nice']), '--property=MemoryHigh=' + service['MemoryHigh'],
            '--property=MemoryMax=' + service['MemoryMax'], '--property=RuntimeMaxSec=1800',
            '--property=TimeoutStopSec=120', '--property=KillMode=mixed',
            '--property=StandardOutput=append:' + str(self.log), '--property=StandardError=append:' + str(self.log),
            *recording_args,
            sys.executable, str(HERE / 'server_runner.py'), '--console', str(self.console),
            self.manifest['wrapper']['path'], *self.manifest['jvm_flags'],
            *(['-XX:StartFlightRecording=settings=profile,dumponexit=true,maxsize=128m,filename=' + str(self.jfr_output)]
              if recording_args else [])], check=True)
        self.wait_log('Done (', 240)
        from c2me_runtime import verify_startup
        verify_startup(
            self.manifest['pregen_mods'] if pregen else self.manifest['mods'],
            (self.server / 'config/c2me.toml').read_text()
                if (self.server / 'config/c2me.toml').exists() else '',
            self.log.read_text())
        group = command('systemctl', 'show', UNIT, '-p', 'ControlGroup', '--value')
        self.cgroup = Path('/sys/fs/cgroup') / group.lstrip('/')
        pids = []
        for process in Path('/proc').iterdir():
            if not process.name.isdigit():
                continue
            try:
                if any(line.endswith(':' + group) for line in (process / 'cgroup').read_text().splitlines()) and \
                        (process / 'cmdline').read_bytes().split(b'\0')[0].endswith(b'/bin/java'):
                    pids.append(int(process.name))
            except (FileNotFoundError, ProcessLookupError):
                pass
        self.pid = unique_java(pids)

    def wait_log(self, pattern, timeout):
        deadline = time.monotonic() + timeout
        while not self.log.exists() or pattern not in self.log.read_text():
            if time.monotonic() > deadline or command('systemctl', 'is-active', UNIT) != 'active':
                raise RuntimeError('bounded functional log condition failed: ' + pattern)
            time.sleep(1)

    def send(self, text):
        if '\n' in text or '\r' in text or len(text.encode()) >= 8192:
            raise ValueError('invalid console command')
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(10)
            connection.connect(str(self.console))
            connection.sendall(text.encode())
            if connection.recv(128) != b'QUEUED\n':
                raise RuntimeError('console command rejected')

    def stop(self):
        try:
            if self.active:
                if command('systemctl', 'show', UNIT, '-p', 'LoadState', '--value') != 'not-found':
                    subprocess.run(['systemctl', 'stop', UNIT], check=True)
                self.active = False
                helper = identity_helper()
                helper.capture(self.server / 'config/DistantHorizons.toml',
                               self.server / 'config/distant-horizons-server-id')
        finally:
            if self.owns_slice:
                maintenance.cleanup_slice()
                self.owns_slice = False

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.stop()
