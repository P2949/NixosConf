"""Bounded reversible DH landmark update on generated disposable terrain."""

import json
from pathlib import Path
import time

from functional_clients import log_offset, wait_for_log_since

START, END = (-320, 300, 0), (-300, 300, 0)


def require_generated_landmark(regions):
    full = {(entry['xPos'], entry['zPos'])
            for name, region in regions.items() if Path(name).parent.name == 'region'
            for entry in region.get('chunk_metadata', [])
            if entry.get('Status') == 'minecraft:full'}
    if not {(-20, 0), (-19, 0)}.issubset(full):
        raise RuntimeError('landmark requires already-generated full chunks')


def verify_air(lab, marker):
    conditions = ' '.join(f'if block {x} 300 0 minecraft:air' for x in range(-320, -299))
    offset = log_offset(lab.log)
    lab.send(f'execute {conditions} run say {marker}')
    wait_for_log_since(lab.log, marker, offset)


def exercise_landmark(lab, client):
    client.wait_joined()
    offset = log_offset(lab.log)
    lab.send('tp @a[name=PerfProbe,limit=1] 0 100 0')
    lab.send('execute positioned 0 100 0 if entity @a[name=PerfProbe,distance=..1] run say QUALIFICATION_DH_ORIGIN')
    wait_for_log_since(lab.log, 'QUALIFICATION_DH_ORIGIN', offset)
    lab.send('forceload add -320 0 -300 0')
    changed = False
    try:
        verify_air(lab, 'QUALIFICATION_DH_LANDMARK_ORIGINAL_AIR')
        # Allow cached-client startup synchronization to settle before mutation.
        time.sleep(20)
        messages = client.output / 'dh-received.jsonl'
        offset = messages.stat().st_size if messages.exists() else 0
        mutation_time = time.monotonic_ns()
        changed = True
        lab.send('fill -320 300 0 -300 300 0 minecraft:gold_block')
        deadline = time.monotonic() + 45
        partial_updates = 0
        while not partial_updates:
            with messages.open('rb') as stream:
                stream.seek(offset)
                lines = stream.read().splitlines()
            # A producer may be midway through its final JSON line.
            for line in lines:
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                partial_updates += message.get('type') == 'FullDataPartialUpdateMessage' and not message.get('exception_type')
            if time.monotonic() >= deadline:
                raise RuntimeError('no DH partial update after distant landmark mutation')
            if not partial_updates:
                time.sleep(.25)
        client.wait_finished()
        return {'mutation_monotonic_ns': mutation_time, 'telemetry_byte_offset': offset,
                'partial_updates_after_mutation': partial_updates,
                'landmark_start': START, 'landmark_end': END,
                'client_origin': [0, 100, 0], 'distance_chunks': 19,
                'original_and_restored_block': 'minecraft:air', 'restored': True}
    finally:
        if changed:
            lab.send('fill -320 300 0 -300 300 0 minecraft:air')
            verify_air(lab, 'QUALIFICATION_DH_LANDMARK_RESTORED_AIR')
        lab.send('forceload remove -320 0 -300 0')


def qualify_realtime(lab, manifest, output, regions, initial_client_pid):
    from pathlib import Path
    import math
    import re
    from functional_dh import dh_outcome, read_dh_messages, VERIFIED_DH_3_3_4_SHA256
    from client_runtime import Client
    from dh_database import inspect_closed_cache
    from qualification_manifest import canonical_bytes
    if not any(mod.get('id') == 'distanthorizons' and mod.get('sha256') == VERIFIED_DH_3_3_4_SHA256 for mod in manifest.get('mods', [])):
        raise RuntimeError('landmark section geometry requires inspected DH 3.3.4 artifact')
    require_generated_landmark(regions)
    if any((lab.server / 'world').rglob('chunks.dat')):
        raise RuntimeError('landmark fixture requires no pre-existing forced-chunk state')
    options = manifest['client']['profiles']['dh-clean']['files']['options.txt']['content']
    render = re.search(r'(?m)^renderDistance:(\d+)$', options)
    if render is None or int(render.group(1)) > 12:
        raise RuntimeError('controlled landmark must be outside vanilla render distance')
    cache = Path(manifest['client']['root']) / 'instances/dh-clean/minecraft/Distant_Horizons_server_data'
    baseline_output = output / 'client-dh' / 'database-before-landmark'
    baseline_output.mkdir(mode=0o700)
    before = inspect_closed_cache(cache, baseline_output,
                                  owner_stopped=not Path(f'/proc/{initial_client_pid}').exists(), requested_sections=((0, -5, 0),))
    client_output = output / 'client-dh-update'
    with Client(manifest, client_output, 'dh-clean', 120) as client:
        receipt = exercise_landmark(lab, client)
        pid = client.pid
    messages = read_dh_messages(client_output / 'dh-received.jsonl')
    heartbeat = json.loads((client_output / 'heartbeat.json').read_text())
    result = json.loads((client_output / 'result.json').read_text())
    elapsed = heartbeat.get('elapsed_seconds')
    if dh_outcome(messages, manifest) != 'PASS' or result != {'result': 'PASS'} or not isinstance(heartbeat.get('connected'), bool) or isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed <= 0:
        raise RuntimeError('DH landmark client completion or protocol evidence failed')
    after = inspect_closed_cache(cache, client_output,
                                 owner_stopped=not Path(f'/proc/{pid}').exists(), requested_sections=((0, -5, 0),))
    # In pinned DH 3.3.4, detail-zero sections span 64 blocks; the landmark
    # occupies section (-5, 0). Compare terrain data, excluding timestamps.
    def landmark_fingerprints(databases):
        return {database['source']: database['requested_section_fingerprints']['0,-5,0']
                for database in databases if '@minecraft@@overworld' in database['source']
                and '0,-5,0' in database['requested_section_fingerprints']}
    before_fingerprints = landmark_fingerprints(before)
    after_fingerprints = landmark_fingerprints(after)
    if not before_fingerprints or set(before_fingerprints) != set(after_fingerprints) or before_fingerprints == after_fingerprints:
        raise RuntimeError('distant landmark did not change its finalized DH terrain section')
    receipt.update({'result': 'PASS', 'database_before': before, 'database_after': after,
                    'client_pid': pid, 'vanilla_render_distance_chunks': int(render.group(1)),
                    'database_content_changed': True})
    evidence = [{'path': database['copy'], 'type': 'sqlite'} for database in before + after]
    evidence.extend({'path': str(client_output / filename), 'type': kind}
                    for filename, kind in (('dh-received.jsonl', 'log'), ('result.json', 'json'),
                                           ('heartbeat.json', 'json'), ('launcher.log', 'log')))
    receipt['evidence'] = evidence
    path = output / 'dh-realtime.json'
    path.write_bytes(canonical_bytes(receipt))
    path.chmod(0o400)
    return receipt
