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
    inspect_maintenance_mode,
    write_post_chunky_proofs,
    qualification_exit_code,
)
from world_semantics import region_occupancy


class ChunkyExtentTests(unittest.TestCase):
    def test_exit_status_propagates_queue_outcomes_and_missing_gates(self):
        references = {gate: {'result': 'PASS'} for gate in
                      ('identity_restart', 'post_chunky_catchup', 'no_unbounded_queues')}
        self.assertEqual(qualification_exit_code(references), 0)
        references['no_unbounded_queues']['result'] = 'FAIL'
        self.assertEqual(qualification_exit_code(references), 1)
        references['no_unbounded_queues']['result'] = 'INCONCLUSIVE'
        self.assertEqual(qualification_exit_code(references), 2)
        self.assertEqual(qualification_exit_code({}), 2)

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


    def test_maintenance_mode_state_requires_exact_runtime_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            server = root / 'survival'
            config = server / 'config'
            mods = server / 'mods'

            config.mkdir(parents=True)
            mods.mkdir()

            artifact = root / 'c2me.jar'
            artifact.write_bytes(b'c2me')

            manifest = {
                'controlled_server_properties': {
                    'pause-when-empty-seconds': 60,
                },
                'dh_pregen_pause_seconds': -1,
                'mode_backup_timers': {
                    'normal': True,
                    'chunky': False,
                    'dh_pregen': False,
                },
                'mods': [
                    {
                        'id': 'c2me',
                        'filename': 'c2me.jar',
                    },
                ],
                'dh_pregen_mods': [
                    {
                        'id': 'c2me',
                        'filename': 'c2me.jar',
                    },
                ],
            }

            class Lab:
                pass

            lab = Lab()
            lab.server = server

            def install_state(
                generator_mode,
                generator_plan,
                pause,
            ):
                (
                    config / 'DistantHorizons.toml'
                ).write_text(
                    '[server]\n'
                    'serverId = 42\n'
                    '[common.worldGenerator]\n'
                    f'chunkGeneratorMode = "{generator_mode}"\n'
                    f'generatorPlan = "{generator_plan}"\n'
                )

                (server / 'server.properties').write_text(
                    f'pause-when-empty-seconds={pause}\n'
                )

                for path in mods.iterdir():
                    path.unlink()

                (mods / 'c2me.jar').symlink_to(artifact)

            install_state(
                'INTERNAL_SERVER',
                'CHUNKS_ONLY',
                -1,
            )
            state = inspect_maintenance_mode(
                lab,
                manifest,
                'dh_pregen',
                '42\n',
            )

            self.assertEqual(
                state['chunk_generator_mode'],
                'INTERNAL_SERVER',
            )
            self.assertEqual(
                state['pause_when_empty_seconds'],
                -1,
            )
            self.assertFalse(
                state['declared_backup_timer_enabled']
            )

            install_state(
                'PRE_EXISTING_ONLY',
                'CHUNKS_ONLY',
                60,
            )
            state = inspect_maintenance_mode(
                lab,
                manifest,
                'normal',
                '42\n',
            )

            self.assertEqual(
                state['chunk_generator_mode'],
                'PRE_EXISTING_ONLY',
            )
            self.assertEqual(
                state['pause_when_empty_seconds'],
                60,
            )
            self.assertTrue(
                state['declared_backup_timer_enabled']
            )

            (mods / 'chunky.jar').symlink_to(artifact)
            with self.assertRaisesRegex(
                RuntimeError,
                'mod inventory mismatch',
            ):
                inspect_maintenance_mode(
                    lab,
                    manifest,
                    'normal',
                    '42\n',
                )

    def test_proofs_bind_both_server_phases_and_use_partial_reference_name(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)

            extent = output / 'chunky-extent.json'
            catchup = output / 'catchup-observation.json'
            pregen = output / 'server-phase-1.log'
            normal = output / 'server-phase-2.log'
            agent = output / 'agent.jar'
            transition = output / 'maintenance-transitions.json'
            dh_pregen = output / 'server-phase-3.log'
            restored_normal = output / 'server-phase-4.log'

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
            transition.write_text('{"result":"PASS"}\n')
            dh_pregen.write_text('dh pregen started\n')
            restored_normal.write_text('normal restored\n')

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
                    transition,
                    dh_pregen,
                    restored_normal,
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

            evidence_by_gate = {
                gate: evidence
                for gate, _, evidence in calls
            }

            for item in (
                (transition, 'json'),
                (dh_pregen, 'log'),
                (restored_normal, 'log'),
            ):
                self.assertIn(
                    item,
                    evidence_by_gate['identity_restart'],
                )
                self.assertNotIn(
                    item,
                    evidence_by_gate['post_chunky_catchup'],
                )
                self.assertNotIn(
                    item,
                    evidence_by_gate['no_unbounded_queues'],
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
                    transition,
                    dh_pregen,
                    restored_normal,
                )


if __name__ == '__main__':
    unittest.main()
