#!/usr/bin/env python3
"""Read-only private runtime provenance. Missing required fields fail capture."""
import json
from datetime import datetime, timezone
import os
import subprocess
import sys
from pathlib import Path


def capture(root=Path('/'), run=subprocess.run):
    def path(value):
        return root / value.lstrip('/')
    def read(value, required=True):
        try:
            text = path(value).read_text().strip()
        except OSError as error:
            if required:
                raise ValueError(f'required observation unreadable: {value}') from error
            return {'status': 'unavailable'}
        return {'status': 'observed', 'value': text}
    def integer(value):
        result=read(value)
        result['value']=int(result['value'])
        return result
    cpu={}
    for line in read('/proc/cpuinfo')['value'].splitlines():
        key, separator, value=line.partition(':')
        if separator and key.strip() not in cpu:
            cpu[key.strip()]=value.strip()
    identity={key:cpu[key] for key in ('vendor_id','cpu family','model','stepping','microcode')}
    policies=[]
    for policy in sorted(path('/sys/devices/system/cpu/cpufreq').glob('policy*')):
        base='/' + str(policy.relative_to(root))
        policies.append({'id':policy.name,**{key:read(base+'/'+key) for key in ('affected_cpus','scaling_driver','scaling_governor','scaling_min_freq','scaling_max_freq','energy_performance_preference')}})
    if not policies:
        raise ValueError('no CPU frequency policies observed')
    rapl='/sys/class/powercap/intel-rapl:0/'
    if read(rapl+'name')['value']!='package-0' or read(rapl+'enabled')['value']!='1':
        raise ValueError('Intel package-0 RAPL is not active')
    limits={}
    for index,expected in [(0,'long_term'),(1,'short_term')]:
        if read(rapl+f'constraint_{index}_name')['value'] != expected:
            raise ValueError('RAPL constraint identity mismatch')
        limits[expected]=integer(rapl+f'constraint_{index}_power_limit_uw')
    temperatures=[]
    for monitor in sorted(path('/sys/class/hwmon').glob('hwmon*')):
        base='/' + str(monitor.relative_to(root))
        if read(base+'/name',False).get('value')!='coretemp':continue
        for sensor in sorted(monitor.glob('temp*_input')):
            stem=sensor.name.removesuffix('_input')
            temperatures.append({'label':read(base+'/'+stem+'_label'),'milliCelsius':integer(base+'/'+stem+'_input'),'criticalMilliCelsius':integer(base+'/'+stem+'_crit')})
    if not temperatures:raise ValueError('no hardware temperature observations')
    throttling={}
    for counter in sorted(path('/sys/devices/system/cpu').glob('cpu[0-9]*/thermal_throttle/*_throttle_count')):
        throttling[str(counter.relative_to(path('/sys/devices/system/cpu')))]=integer('/'+str(counter.relative_to(root)))
    if not throttling:raise ValueError('no thermal throttle counters observed')
    maintenance={}
    for unit in ['nix-gc.service','btrfs-scrub--.service','fstrim.service']:
        result=run(['systemctl','is-active',unit],text=True,capture_output=True)
        state=result.stdout.strip()
        if state not in ('active','inactive','failed','activating','deactivating'):
            raise ValueError(f'maintenance state unknown: {unit}')
        maintenance[unit]=state
    systems={name:os.path.realpath(path('/run/'+name+'-system')) for name in ('current','booted')}
    if any(not value.startswith('/nix/store/') for value in systems.values()):
        raise ValueError('unresolved current/booted system')
    return {'schemaVersion':1,'capturedAt':datetime.now(timezone.utc).isoformat(),'kind':'nixos-experiment-runtime','host':read('/proc/sys/kernel/hostname'),
        'bootId':read('/proc/sys/kernel/random/boot_id'),'systems':systems,
        'kernel':{'release':read('/proc/sys/kernel/osrelease'),'commandLine':read('/proc/cmdline')},
        'cpu':{'identity':identity,'online':read('/sys/devices/system/cpu/online'),'smt':read('/sys/devices/system/cpu/smt/active'),'policies':policies,'packagePowerMicrowatts':limits,'intelPstate':{key:read('/sys/devices/system/cpu/intel_pstate/'+key,False) for key in ('status','no_turbo','min_perf_pct','max_perf_pct','hwp_dynamic_boost')},'vulnerabilities':{p.name:read('/'+str(p.relative_to(root))) for p in sorted(path('/sys/devices/system/cpu/vulnerabilities').glob('*'))}},
        'memory':{'transparentHugePages':read('/sys/kernel/mm/transparent_hugepage/enabled'),'numaBalancing':read('/proc/sys/kernel/numa_balancing'),'meminfo':read('/proc/meminfo'),'swaps':read('/proc/swaps')},
        'temperatures':temperatures,'thermalThrottleCounters':throttling,'maintenance':maintenance}



def validate_control(snapshot, declared_control, physical_target):
    """Benchmark admission requires a physically booted exact declared control."""
    if snapshot['systems'] != {'current': declared_control, 'booted': declared_control}:
        raise ValueError('current/booted systems do not match declared control')
    identity = snapshot['cpu']['identity']
    observed = {'hostname': snapshot['host']['value'], 'cpuVendor': identity['vendor_id'],
                'cpuFamily': identity['cpu family'], 'cpuModel': identity['model']}
    if observed != physical_target:
        raise ValueError('designated physical target mismatch')
    validate_interval(snapshot, snapshot)


def validate_interval(before,after):
    for key in ('host','bootId','systems','kernel','cpu'):
        if before[key]!=after[key]:raise ValueError(f'runtime identity/policy changed: {key}')
    if any(state not in ('inactive','failed') for snapshot in (before,after) for state in snapshot['maintenance'].values()):
        raise ValueError('maintenance overlaps measurement')
    for key in ('transparentHugePages','numaBalancing'):
        if before['memory'][key]!=after['memory'][key]:raise ValueError(f'memory policy changed: {key}')
    if before['thermalThrottleCounters']!=after['thermalThrottleCounters']:
        raise ValueError('thermal throttle counters changed')
    for snapshot in (before,after):
        if any(sensor['milliCelsius']['value']>=sensor['criticalMilliCelsius']['value'] for sensor in snapshot['temperatures']):
            raise ValueError('hardware critical temperature reached')


if __name__=='__main__':
    try:
        print(json.dumps(capture(),sort_keys=True,indent=2))
    except (ValueError,KeyError,OSError) as error:
        print(f'Runtime capture refused: {error}',file=sys.stderr)
        sys.exit(1)
