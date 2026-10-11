"""Bounded reversible DH landmark update on generated disposable terrain."""

import json
import time

from functional_clients import log_offset, wait_for_log_since

START, END = (-320, 300, 0), (-300, 300, 0)


def require_generated_landmark(regions):
    full = {(entry['xPos'], entry['zPos'])
            for name, region in regions.items() if '/region/' in name
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
