from pathlib import Path
import json
import struct
import tempfile
import unittest
from unittest.mock import patch

from post_chunky import (
    chunk_bounds,
    generation_extent,
    in_target,
    require_ungenerated,
    terrain_chunks,
    write_post_chunky_proofs,
)
from world_semantics import region_occupancy


class ChunkyExtentTests(unittest.TestCase):
    def test_target_must_be_ungenerated_before_start(self):
        require_ungenerated({'region/r.0.0.mca': {'chunks': [(0, 0)]}}, chunk_bounds())
        with self.assertRaisesRegex(RuntimeError, 'already generated'):
            require_ungenerated({'region/r.16.16.mca': {'chunks': [(512, 512)]}}, chunk_bounds())

    def test_root_overworld_and_26_3_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for layout in ('region', 'dimensions/minecraft/overworld/region'):
                region = root / layout
                region.mkdir(parents=True)
                data = bytearray(12288)
                struct.pack_into('>I', data, 0, (2 << 8) | 1)
                struct.pack_into('>I', data, 8192, 2)
                data[8196:8198] = b'\x02x'
                (region / 'r.16.16.mca').write_bytes(data)
                self.assertEqual(terrain_chunks(region_occupancy(root)), {(512, 512)})
            self.assertFalse(terrain_chunks({'DIM-1/region/r.16.16.mca': {'chunks': [(512, 512)]}}))

    def test_block_radius_and_negative_floor_division(self):
        self.assertEqual(chunk_bounds(), (496, 528, 496, 528))
        self.assertTrue(in_target((496, 528), chunk_bounds()))
        self.assertFalse(in_target((480, 544), chunk_bounds()))
        self.assertEqual(chunk_bounds(-1, -1, 16), (-2, 0, -2, 0))
        with self.assertRaises(ValueError):
            chunk_bounds(radius=0)

    def test_only_upstream_stage_dependencies_allow_protochunk_halo(self):
        chunks = [(x, z) for x in range(496, 529) for z in range(496, 529)]
        metadata = [{'xPos': x, 'zPos': z, 'Status': 'minecraft:full'} for x, z in chunks]
        chunks.append((485, 485))
        metadata.append({'xPos': 485, 'zPos': 485, 'Status': 'minecraft:structure_starts'})
        regions = {'region/r.16.16.mca': {'chunks': chunks, 'chunk_metadata': metadata}}
        policy = {'minecraft:full': 0, 'minecraft:structure_starts': 11}
        result = generation_extent({}, regions, chunk_bounds(), policy)
        self.assertEqual(result['result'], 'PASS')
        self.assertEqual(result['new_full_chunks'], 1089)
        metadata[-1]['Status'] = 'minecraft:full'
        self.assertEqual(generation_extent({}, regions, chunk_bounds(), policy)['result'], 'FAIL')
        metadata[-1]['Status'] = 'minecraft:unknown'
        self.assertEqual(generation_extent({}, regions, chunk_bounds(), policy)['result'], 'FAIL')
        metadata[-1].update(Status='minecraft:structure_starts', xPos=484)
        chunks[-1] = (484, 485)
        self.assertEqual(generation_extent({}, regions, chunk_bounds(), policy)['result'], 'FAIL')


    def test_proofs_bind_both_server_phases_and_use_partial_reference_name(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)

            extent = output / 'chunky-extent.json'
            catchup = output / 'catchup-observation.json'
            pregen = output / 'server-phase-1.log'
            normal = output / 'server-phase-2.log'
            agent = output / 'agent.jar'

            extent.write_text('{}')
            catchup.write_text(
                json.dumps({
                    'result': 'PASS',
                })
            )
            pregen.write_text(
                'Chunky completed\n'
            )
            normal.write_text(
                'normal catchup completed\n'
            )
            agent.write_bytes(
                b'agent'
            )

            class Lab:
                active = False
                server = (
                    output
                    / 'world-clone/survival'
                )

            manifest = {
                'baseline': {
                    'subvolume_uuid': 'baseline',
                },
            }

            queue_result = {
                'result': 'PASS',
            }

            calls = []

            def fake_write_proof(
                manifest,
                gate,
                path,
                evidence,
                result,
            ):
                calls.append(
                    (
                        gate,
                        result,
                        list(evidence),
                    )
                )

                path.write_text('{}')

                return {
                    'result': result,
                    'evidence': str(path),
                    'sha256': 'test-' + gate,
                }

            with patch(
                'post_chunky.write_proof',
                side_effect=fake_write_proof,
            ):
                references = write_post_chunky_proofs(
                    manifest,
                    output,
                    Lab,
                    agent,
                    queue_result,
                    1089,
                    1089,
                    '123',
                    '123',
                    extent,
                    pregen,
                    normal,
                )

            self.assertEqual(
                set(references),
                {
                    'identity_restart',
                    'post_chunky_catchup',
                    'no_unbounded_queues',
                },
            )

            for _, _, evidence in calls:
                self.assertIn(
                    (pregen, 'log'),
                    evidence,
                )

                self.assertIn(
                    (normal, 'log'),
                    evidence,
                )

            self.assertTrue(
                (
                    output
                    / 'post-chunky-reference.json'
                ).is_file()
            )

            self.assertFalse(
                (
                    output
                    / 'functional-acceptance.json'
                ).exists()
            )

            Lab.active = True

            with self.assertRaisesRegex(
                RuntimeError,
                'stopped functional server',
            ):
                write_post_chunky_proofs(
                    manifest,
                    output,
                    Lab,
                    agent,
                    queue_result,
                    1089,
                    1089,
                    '123',
                    '123',
                    extent,
                    pregen,
                    normal,
                )


if __name__ == '__main__':
    unittest.main()
