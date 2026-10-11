"""Bounded Chunky-to-normal-DH catch-up and identity restart qualification."""

import argparse
import json
import os
from pathlib import Path
import re
import signal
import time
import tomllib

from functional_runtime import Lab
from observe_queues import observe
from qualification_manifest import canonical_bytes, sha256
from qualification_proof import write_proof
from world_semantics import region_occupancy, no_unwanted_generation
import maintenance


def terrain_chunks(regions):
    return {tuple(pos) for name, region in regions.items()
            if name.startswith('dimensions/minecraft/overworld/region/') for pos in region['chunks']}


def execute(manifest, output, agent):
    if str(agent) != manifest['queue_agent']['path'] or sha256(agent) != manifest['queue_agent']['sha256']:
        raise ValueError('queue observer must be the immutable Nix-built candidate artifact')
    lab = Lab(manifest, output)
    (output / 'candidate-manifest.json').write_bytes(canonical_bytes(manifest))
    try:
        maintenance.enter(output)
        with lab:
            before = region_occupancy(lab.server / 'world')
            lab.start(pregen=True)
            effective = tomllib.loads((lab.server / 'config/DistantHorizons.toml').read_text())
            if effective['common']['worldGenerator']['generatorPlan'] != 'DISABLED':
                raise RuntimeError('Chunky maintenance DH generation not disabled')
            lab.send('chunky start minecraft:overworld square 8192 8192 256')
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
            generated = region_occupancy(lab.server / 'world')
            added = terrain_chunks(generated) - terrain_chunks(before)
            if len(added) < 1024 or any(not (480 <= x <= 544 and 480 <= z <= 544) for x, z in added):
                raise RuntimeError('unexpected bounded Chunky generation extent')
            identity_path = lab.server / 'config/distant-horizons-server-id'
            identity_before = identity_path.read_text()
            maintenance.refresh()
            lab.start()
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
            after = region_occupancy(lab.server / 'world')
            if not no_unwanted_generation(generated, after):
                raise RuntimeError('normal zero-player DH generated unexpected terrain')
            receipt = output / 'workload.json'
            receipt.write_text(json.dumps({'result': queue_result['result'], 'processed': processed,
                'new_terrain_chunks': len(added), 'identity_before': int(identity_before),
                'identity_after': int(identity_after), 'queue_observation': queue_result,
                'agent_sha256': sha256(agent), 'production_data_touched': False}, indent=2) + '\n')
            evidence = [(receipt, 'json'), (output / 'catchup-observation.json', 'json'),
                        (lab.log, 'log'), (agent, 'binary')]
            references = {gate: write_proof(manifest, gate, output / (gate + '-proof.json'), evidence,
                         'PASS' if gate == 'identity_restart' else queue_result['result'])
                          for gate in ('identity_restart', 'post_chunky_catchup', 'no_unbounded_queues')}
            (output / 'functional-acceptance.json').write_text(json.dumps(references, indent=2) + '\n')
            return references
    finally:
        try:
            lab.stop()
        finally:
            if (output / 'maintenance.json').exists():
                maintenance.restore(output)
                if (output / 'guard-armed').exists():
                    maintenance.disarm()


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
    print(json.dumps(execute(json.loads(args.manifest.read_text()), args.output, args.agent)))
