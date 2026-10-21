"""Check real installed GameMode hooks against LACT and physical AMDGPU state."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time

ROOT = Path('/sys/bus/pci/devices/0000:03:00.0')
RECEIPT = Path(os.environ['XDG_RUNTIME_DIR']) / 'gamemode-gpu-profile/state.json'
OUTPUT = Path('/var/tmp/gpu-dpm-preflight/gamemode-smoke.json')
records = []


def api(command, args):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(5)
        conn.connect('/run/lactd.sock')
        conn.sendall((json.dumps({'command': command, 'args': args})+'\n').encode())
        reply = json.loads(conn.makefile('r').readline(1024*1024))
    assert reply['status'] == 'ok', reply
    return reply.get('data')


def readback():
    current = api('list_profiles', {'include_state': True})
    modes = (ROOT/'pp_power_profile_mode').read_text()
    clocks = (ROOT/'pp_od_clk_voltage').read_bytes().replace(b'\x00', b'').decode()
    hw = next((ROOT/'hwmon').iterdir())
    return {
        'profile': current['current_profile'],
        'auto_switch': current['auto_switch'],
        'profiles': sorted(current['profiles']),
        'level': (ROOT/'power_dpm_force_performance_level').read_text().strip(),
        'mode': int(re.search(r'^\s*(\d+)\s+\w+\*', modes, re.M).group(1)),
        'cap_uw': int((hw/'power1_cap').read_text()),
        'voltage_offset_mv': int(re.search(r'OD_VDDGFX_OFFSET:\s*(-?\d+)mv', clocks, re.I).group(1)),
        'clocks': clocks,
        'fan_curve': (ROOT/'gpu_od/fan_ctrl/fan_curve').read_text(),
        'zero_rpm': (ROOT/'gpu_od/fan_ctrl/fan_zero_rpm_enable').read_text(),
        'temps_c': [int((hw/f'temp{i}_input').read_text())/1000 for i in (1,2,3)],
    }


def wait_for(label, profile, level, mode, cap, offset):
    expected = (profile, level, mode, cap, offset)
    until = time.monotonic()+40
    actual = None
    while time.monotonic()<until:
        actual = readback()
        values = tuple(actual[k] for k in ('profile','level','mode','cap_uw','voltage_offset_mv'))
        if values == expected:
            assert not actual['auto_switch']
            assert actual['profiles'] == ['Daily','Gaming','Stock']
            records.append({'label':label, 'result':'PASS', **actual})
            print(label+': PASS', flush=True)
            return actual
        time.sleep(.25)
    raise AssertionError(f'{label}: expected {expected}, got {actual}')


def select(profile):
    api('set_profile', {'name':profile,'auto_switch':False})


assert os.geteuid() != 0, 'GameMode must run as the desktop user'
assert not RECEIPT.exists(), 'Existing GameMode claim must be resolved first'
initial = wait_for('installed Daily', 'Daily','manual',2,238_000_000,-150)
status = 'FAIL'
client = None
try:
    for previous in ('Daily','Stock'):
        select(previous)
        if previous == 'Stock':
            wait_for('Stock before GameMode','Stock','auto',0,340_000_000,0)
        client = subprocess.Popen(['gamemoderun','sleep','10'])
        gaming = wait_for(previous+' -> GameMode Gaming','Gaming','manual',1,238_000_000,-150)
        assert gaming['fan_curve'] == initial['fan_curve']
        assert gaming['zero_rpm'] == initial['zero_rpm']
        receipt = json.loads(RECEIPT.read_text())
        assert receipt['previous'] == previous, receipt
        client.wait(timeout=20)
        assert client.returncode == 0
        client = None
        if previous == 'Daily':
            restored = wait_for('GameMode -> Daily','Daily','manual',2,238_000_000,-150)
            assert restored['fan_curve'] == initial['fan_curve']
            assert restored['zero_rpm'] == initial['zero_rpm']
        else:
            wait_for('GameMode -> Stock','Stock','auto',0,340_000_000,0)
        until = time.monotonic()+5
        while RECEIPT.exists() and time.monotonic()<until:
            time.sleep(.1)
        assert not RECEIPT.exists(), 'GameMode receipt was not cleared'
    status = 'PASS'
finally:
    if client is not None:
        client.terminate()
        client.wait(timeout=10)
        time.sleep(8)
    select('Daily')
    wait_for('final Daily','Daily','manual',2,238_000_000,-150)
    OUTPUT.write_text(json.dumps({'result':status,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'running_system':str(Path('/run/current-system').resolve()),'records':records},indent=2)+'\n')
