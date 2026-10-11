"""Bounded disposable GUI clients for automated functional proof, owned by systemd."""

import json
import os
from pathlib import Path
import pwd
import subprocess
import time

import maintenance
from client_identity import verify
from functional_runtime import command
from qualification_manifest import controlled_path


class Client:
    def __init__(self, manifest, output, profile, duration, *, fresh_cache=False):
        if profile not in ('dh-clean', 'no-dh') or not 1 <= duration <= 600:
            raise ValueError('bounded functional client profile/duration required')
        if command('systemctl', 'show', maintenance.CLIENT, '-p', 'LoadState', '--value') != 'not-found':
            raise RuntimeError('qualification client unit name occupied')
        self.identity = manifest['client']
        self.instance = verify(self.identity, profile)
        self.output = controlled_path(output, Path('/persist'))
        if not self.output.parent.name.startswith('minecraft-performance-functional-'):
            raise ValueError('client evidence must be directly inside functional output')
        self.output.mkdir(mode=0o700)
        account = pwd.getpwnam('p2949')
        os.chown(self.output, account.pw_uid, account.pw_gid)
        self.profile = profile
        self.duration = duration
        self.active = False
        self.deadline = time.monotonic() + duration + 240
        if fresh_cache:
            cache = self.instance / 'minecraft/Distant_Horizons_server_data'
            if os.path.lexists(cache):
                controlled_path(cache, self.identity['root'], existing=True)
                # Preserve earlier raw client data; never erase production/profile state.
                cache.rename(self.output / 'previous-client-cache')
            if cache.exists():
                raise RuntimeError('fresh client cache preparation failed')

    def start(self):
        verify(self.identity, self.profile)
        variables = {'MINECRAFT_PROBE_OUTPUT': str(self.output),
                     'MINECRAFT_PROBE_DURATION': str(self.duration)}
        for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS', 'XAUTHORITY'):
            if key in os.environ:
                variables[key] = os.environ[key]
        if not variables.get('DISPLAY') and not variables.get('WAYLAND_DISPLAY'):
            raise RuntimeError('GUI session environment required')
        self.active = True
        subprocess.run(['systemd-run', '--collect', '--unit=' + maintenance.CLIENT,
            '--property=User=p2949', '--property=Group=users', '--property=KillMode=mixed',
            '--property=RuntimeMaxSec=' + str(self.duration + 240), '--property=TimeoutStopSec=30',
            '--property=StandardOutput=append:' + str(self.output / 'launcher.log'),
            '--property=StandardError=append:' + str(self.output / 'launcher.log'),
            *('--setenv=' + key + '=' + value for key, value in variables.items()),
            self.identity['launcher']['path'], '--dir', self.identity['root'],
            '--launch', self.profile, '--offline', 'PerfProbe', '--server', '127.0.0.1:25576'], check=True)

    def joined(self):
        heartbeat = self.output / 'heartbeat.json'
        try:
            return heartbeat.exists() and json.loads(heartbeat.read_text()).get('connected') is True
        except json.JSONDecodeError:
            return False

    def wait_joined(self):
        deadline = time.monotonic() + 180
        while not self.joined():
            if time.monotonic() >= deadline or command('systemctl', 'is-active', maintenance.CLIENT) != 'active':
                raise RuntimeError('functional client failed automatic login')
            time.sleep(1)
        pid = int((self.output / 'pid').read_text())
        self.pid = pid
        group = command('systemctl', 'show', maintenance.CLIENT, '-p', 'ControlGroup', '--value')
        if not any(line.endswith(':' + group) for line in Path(f'/proc/{pid}/cgroup').read_text().splitlines()):
            raise RuntimeError('client escaped qualification service ownership')
        arguments = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        if (arguments[0].decode() != self.identity['java']['path']
                or b'-XX:+UseZGC' not in arguments or b'-Xmx8192m' not in arguments):
            raise RuntimeError('actual client Java/collector/heap differs from manifest')

    def wait_finished(self):
        result = self.output / 'result.json'
        while not result.exists():
            if time.monotonic() >= self.deadline:
                raise RuntimeError('bounded client completion timeout')
            time.sleep(1)
        if json.loads(result.read_text()).get('result') != 'PASS':
            raise RuntimeError('functional client probe failed')
        deadline = time.monotonic() + 30
        while Path(f'/proc/{self.pid}').exists():
            if time.monotonic() >= deadline:
                raise RuntimeError('client JVM did not exit cleanly after probe completion')
            time.sleep(.2)
        self.stop()

    def stop(self):
        if self.active:
            if command('systemctl', 'show', maintenance.CLIENT, '-p', 'LoadState', '--value') != 'not-found':
                subprocess.run(['systemctl', 'stop', maintenance.CLIENT], check=True)
            self.active = False
            # Prism/DH rewrite these disposable inputs during normal shutdown.
            # Restore frozen templates for a later run of the same candidate.
            for filename, entry in self.identity['profiles'][self.profile]['files'].items():
                path = controlled_path(self.instance / 'minecraft' / filename,
                                       self.identity['root'], existing=True)
                path.write_text(entry['content'])

    def __enter__(self):
        try:
            self.start()
        except BaseException:
            self.stop()
            raise
        return self

    def __exit__(self, *exception):
        self.stop()
