"""Bounded Chunky-to-normal-DH catch-up and identity restart qualification."""

import argparse
import json
import os
from pathlib import Path
import re
import signal
import sys
import time
import tomllib

from functional_runtime import Lab
from observe_queues import observe
from qualification_manifest import canonical_bytes, sha256
from qualification_proof import write_proof
from world_semantics import region_occupancy, no_unwanted_generation
import maintenance

CENTER_X_BLOCK = 8192
CENTER_Z_BLOCK = 8192
RADIUS_BLOCKS = 256


def chunk_bounds(center_x=CENTER_X_BLOCK, center_z=CENTER_Z_BLOCK, radius=RADIUS_BLOCKS):
    if radius <= 0:
        raise ValueError('positive block radius required')
    return ((center_x - radius) // 16, (center_x + radius) // 16,
            (center_z - radius) // 16, (center_z + radius) // 16)


def in_target(position, bounds):
    x, z = position
    low_x, high_x, low_z, high_z = bounds
    return low_x <= x <= high_x and low_z <= z <= high_z


def terrain_chunks(regions):
    return {tuple(pos) for name, region in regions.items()
            if name.startswith(('region/', 'dimensions/minecraft/overworld/region/'))
            for pos in region['chunks']}


def require_ungenerated(regions, bounds):
    if any(in_target(position, bounds) for position in terrain_chunks(regions)):
        raise RuntimeError('Chunky target already generated in frozen baseline')


def generation_extent(before, after, bounds, dependency_radii):
    previous = terrain_chunks(before)
    added = terrain_chunks(after) - previous
    full = set()
    stages = {}
    violations = []
    for name, region in after.items():
        if not name.startswith(('region/', 'dimensions/minecraft/overworld/region/')):
            continue
        for chunk in region['chunk_metadata']:
            position = (chunk['xPos'], chunk['zPos'])
            if position not in added:
                continue
            status = chunk['Status']
            radius = dependency_radii.get(status)
            stages[status] = stages.get(status, 0) + 1
            if radius is None or not in_target(position,
                    (bounds[0] - radius, bounds[1] + radius, bounds[2] - radius, bounds[3] + radius)):
                violations.append({'position': position, 'status': status})
            if status == 'minecraft:full':
                full.add(position)
    if sum(stages.values()) != len(added) or dependency_radii.get('minecraft:full') != 0:
        raise ValueError('incomplete generation status/dependency evidence')
    return {'result': 'FAIL' if violations or len(full) < 1024 else 'PASS',
            'allowed_full_chunk_bounds': bounds, 'new_chunk_entries': len(added),
            'new_full_chunks': len(full), 'new_chunks_by_status': stages,
            'dependency_radius_chunks': dependency_radii, 'violations': violations}



def read_server_properties(path):
    properties = {}
    for line_number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if not separator or not key or key in properties:
            raise ValueError(
                f'invalid or duplicate server property on line {line_number}'
            )
        properties[key] = value
    return properties


def expected_mod_filenames(manifest, inventory_key):
    inventory = manifest[inventory_key]
    filenames = {entry['filename'] for entry in inventory}
    if len(filenames) != len(inventory):
        raise ValueError('duplicate maintenance mod filename')
    if manifest.get('server_tick_probe'):
        filenames.add('server-tick-probe.jar')
    return filenames


def inspect_maintenance_mode(lab, manifest, mode, expected_identity):
    expected = {
        'normal': {
            'inventory': 'mods',
            'generator_mode': 'PRE_EXISTING_ONLY',
            'generator_plan': 'CHUNKS_ONLY',
            'pause_seconds': manifest['controlled_server_properties'][
                'pause-when-empty-seconds'
            ],
            'declared_backup_timer_enabled': True,
        },
        'dh_pregen': {
            'inventory': 'dh_pregen_mods',
            'generator_mode': 'INTERNAL_SERVER',
            'generator_plan': 'CHUNKS_ONLY',
            'pause_seconds': manifest['dh_pregen_pause_seconds'],
            'declared_backup_timer_enabled': False,
        },
    }
    if mode not in expected:
        raise ValueError('unsupported maintenance transition mode')

    wanted = expected[mode]

    policy = tomllib.loads(
        (lab.server / 'config/DistantHorizons.toml').read_text()
    )
    generator = policy['common']['worldGenerator']

    if (
        generator.get('chunkGeneratorMode') != wanted['generator_mode']
        or generator.get('generatorPlan') != wanted['generator_plan']
    ):
        raise RuntimeError(mode + ' DH generator policy mismatch')

    if int(policy['server']['serverId']) != int(expected_identity):
        raise RuntimeError(mode + ' DH identity mismatch')

    properties = read_server_properties(
        lab.server / 'server.properties'
    )
    if (
        properties.get('pause-when-empty-seconds')
        != str(wanted['pause_seconds'])
    ):
        raise RuntimeError(mode + ' pause policy mismatch')

    entries = list((lab.server / 'mods').iterdir())
    if any(
        not path.is_symlink() or not path.name.endswith('.jar')
        for path in entries
    ):
        raise RuntimeError(
            mode + ' mod directory contains unexpected entry'
        )

    actual_mods = {path.name for path in entries}
    expected_mods = expected_mod_filenames(
        manifest,
        wanted['inventory'],
    )
    if actual_mods != expected_mods:
        raise RuntimeError(mode + ' mod inventory mismatch')

    if (
        mode == 'dh_pregen'
        and any(
            entry.get('id') == 'chunky'
            for entry in manifest[wanted['inventory']]
        )
    ):
        raise RuntimeError(
            'DH pregen inventory unexpectedly contains Chunky'
        )

    timer = manifest['mode_backup_timers'].get(mode)
    if (
        type(timer) is not bool
        or timer != wanted['declared_backup_timer_enabled']
    ):
        raise RuntimeError(mode + ' backup timer policy mismatch')

    return {
        'mode': mode,
        'server_id': int(expected_identity),
        'chunk_generator_mode': generator['chunkGeneratorMode'],
        'generator_plan': generator['generatorPlan'],
        'pause_when_empty_seconds': int(
            properties['pause-when-empty-seconds']
        ),
        # This is the frozen Nix policy. The disposable functional server
        # itself does not own a separate backup timer.
        'declared_backup_timer_enabled': timer,
        'mods': sorted(actual_mods),
    }


def write_post_chunky_proofs(
    manifest,
    output,
    lab,
    agent,
    queue_result,
    processed,
    added_count,
    identity_before,
    identity_after,
    extent,
    pregen_log,
    normal_log,
    transition_receipt,
    dh_pregen_log,
    restored_normal_log,
):
    if lab.active:
        raise RuntimeError(
            'post-Chunky proofs require stopped functional server'
        )

    catchup = output / 'catchup-observation.json'
    receipt = output / 'workload.json'

    receipt.write_text(json.dumps({
        'result': queue_result['result'],
        'processed': processed,
        'new_terrain_chunks': added_count,
        'identity_before': int(identity_before),
        'identity_after': int(identity_after),
        'queue_observation': queue_result,
        'agent_sha256': sha256(agent),
        'server_world': str(lab.server),
        'baseline_uuid': manifest['baseline']['subvolume_uuid'],
    }, indent=2) + '\n')

    for artifact in (
        receipt,
        catchup,
        extent,
        pregen_log,
        normal_log,
        transition_receipt,
        dh_pregen_log,
        restored_normal_log,
    ):
        artifact.chmod(0o400)

    evidence = [
        (receipt, 'json'),
        (catchup, 'json'),
        (extent, 'json'),
        (pregen_log, 'log'),
        (normal_log, 'log'),
        (agent, 'binary'),
    ]

    identity_evidence = evidence + [
        (transition_receipt, 'json'),
        (dh_pregen_log, 'log'),
        (restored_normal_log, 'log'),
    ]

    references = {
        gate: write_proof(
            manifest,
            gate,
            output / (gate + '-proof.json'),
            (
                identity_evidence
                if gate == 'identity_restart'
                else evidence
            ),
            (
                'PASS'
                if gate == 'identity_restart'
                else queue_result['result']
            ),
        )
        for gate in (
            'identity_restart',
            'post_chunky_catchup',
            'no_unbounded_queues',
        )
    }

    reference_path = (
        output
        / 'post-chunky-reference.json'
    )

    reference_path.write_bytes(
        canonical_bytes(references)
    )
    reference_path.chmod(0o400)

    return references


def execute(manifest, output, agent):
    if str(agent) != manifest['queue_agent']['path'] or sha256(agent) != manifest['queue_agent']['sha256']:
        raise ValueError('queue observer must be the immutable Nix-built candidate artifact')
    lab = Lab(manifest, output)
    (output / 'candidate-manifest.json').write_bytes(canonical_bytes(manifest))
    try:
        maintenance.enter(output)
        with lab:
            before = region_occupancy(lab.server / 'world', include_status=True)
            bounds = chunk_bounds()
            require_ungenerated(before, bounds)
            lab.start(pregen=True)
            pregen_log = lab.log
            effective = tomllib.loads((lab.server / 'config/DistantHorizons.toml').read_text())
            if effective['common']['worldGenerator']['generatorPlan'] != 'DISABLED':
                raise RuntimeError('Chunky maintenance DH generation not disabled')
            lab.send(f'chunky start minecraft:overworld square {CENTER_X_BLOCK} {CENTER_Z_BLOCK} {RADIUS_BLOCKS}')
            deadline = time.monotonic() + 1200
            pattern = re.compile(r'Task finished for minecraft:overworld\. Processed: ([\d,]+) chunks \(([\d.]+)%\)')
            while not (completed := pattern.search(lab.log.read_text())):
                if time.monotonic() >= deadline:
                    raise RuntimeError('bounded Chunky completion timeout')
                maintenance.refresh()
                time.sleep(5)
            processed = int(completed[1].replace(',', ''))
            if float(completed[2]) != 100 or processed < 1024:
                raise RuntimeError('incomplete representative Chunky workload')
            lab.stop()
            generated = region_occupancy(lab.server / 'world', include_status=True)
            added = terrain_chunks(generated) - terrain_chunks(before)
            extent = output / 'chunky-extent.json'
            extent_result = generation_extent(before, generated, bounds,
                              manifest['generation_bounds']['dependency_radius_chunks'])
            extent_result.update(block_center=[CENTER_X_BLOCK, CENTER_Z_BLOCK], radius_blocks=RADIUS_BLOCKS)
            extent.write_text(json.dumps(extent_result, indent=2) + '\n')
            if extent_result['result'] != 'PASS' or extent_result['new_full_chunks'] != processed:
                raise RuntimeError('unexpected bounded Chunky generation extent')
            identity_path = lab.server / 'config/distant-horizons-server-id'
            identity_before = identity_path.read_text()
            maintenance.refresh()
            lab.start()
            normal_log = lab.log
            actual = tomllib.loads((lab.server / 'config/DistantHorizons.toml').read_text())
            if actual['server']['serverId'] != int(identity_before):
                raise RuntimeError('DH identity changed during maintenance-to-normal restart')
            if any(actual['common']['worldGenerator'][key] != value for key, value in
                    {'chunkGeneratorMode': 'PRE_EXISTING_ONLY', 'generatorPlan': 'CHUNKS_ONLY'}.items()):
                raise RuntimeError('normal DH generator policy mismatch')
            lab.wait_log('pausing', 240)
            queue_result = observe(lab, agent, output / 'catchup-observation.json')
            lab.stop()
            identity_after = identity_path.read_text()
            if identity_before != identity_after:
                raise RuntimeError('DH identity changed on final stop')
            after = region_occupancy(lab.server / 'world', include_status=True)
            if not no_unwanted_generation(generated, after):
                raise RuntimeError('normal zero-player DH generated unexpected terrain')

            # The no-unwanted-generation assertion deliberately ends before
            # INTERNAL_SERVER is enabled: DH-pregen is allowed to generate
            # vanilla chunks by design.
            transition_identity = identity_after

            maintenance.refresh()
            lab.start(mode='dh_pregen')
            dh_pregen_log = lab.log
            dh_pregen_state = inspect_maintenance_mode(
                lab,
                manifest,
                'dh_pregen',
                transition_identity,
            )
            lab.stop()

            identity_after_dh_pregen = identity_path.read_text()
            if identity_after_dh_pregen != transition_identity:
                raise RuntimeError(
                    'DH identity changed during DH-pregen maintenance mode'
                )

            maintenance.refresh()
            lab.start(mode='normal')
            restored_normal_log = lab.log
            restored_normal_state = inspect_maintenance_mode(
                lab,
                manifest,
                'normal',
                transition_identity,
            )
            lab.stop()

            identity_final = identity_path.read_text()
            if identity_final != transition_identity:
                raise RuntimeError(
                    'DH identity changed after restoring normal mode'
                )

            transition_receipt = output / 'maintenance-transitions.json'
            transition_receipt.write_bytes(canonical_bytes({
                'result': 'PASS',
                'identity_before_dh_pregen': int(transition_identity),
                'identity_after_dh_pregen': int(
                    identity_after_dh_pregen
                ),
                'identity_after_normal_restore': int(identity_final),
                'dh_pregen': dh_pregen_state,
                'restored_normal': restored_normal_state,
            }))

            return write_post_chunky_proofs(
                manifest,
                output,
                lab,
                agent,
                queue_result,
                processed,
                len(added),
                identity_before,
                identity_final,
                extent,
                pregen_log,
                normal_log,
                transition_receipt,
                dh_pregen_log,
                restored_normal_log,
            )
    finally:
        try:
            lab.stop()
        finally:
            if (output / 'maintenance.json').exists():
                maintenance.restore(output)
                if (output / 'guard-armed').exists():
                    maintenance.disarm()


def qualification_exit_code(references):
    outcomes = {reference.get('result') for reference in references.values()}
    if 'FAIL' in outcomes:
        return 1
    required = {'identity_restart', 'post_chunky_catchup', 'no_unbounded_queues'}
    return 0 if set(references) == required and outcomes == {'PASS'} else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--agent', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('root required')
    os.umask(0o077)
    def terminate(signum, frame):
        raise SystemExit('functional qualification interrupted')
    signal.signal(signal.SIGTERM, terminate)
    references = execute(json.loads(args.manifest.read_text()), args.output, args.agent)
    print(json.dumps(references))
    sys.exit(qualification_exit_code(references))
