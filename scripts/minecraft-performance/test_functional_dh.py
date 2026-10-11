import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from functional_dh import (
    dh_outcome,
    execute,
    generation_outcome,
    qualification_exit_code,
    VERIFIED_DH_3_3_4_SHA256,
    read_dh_messages,
)


class FunctionalDhTests(unittest.TestCase):
    def test_exit_status_requires_both_gates_and_propagates_failure(self):
        references = {
            'dh_functional': {'result': 'PASS'},
            'no_unwanted_generation': {'result': 'PASS'},
        }
        self.assertEqual(qualification_exit_code(references), 0)
        references['dh_functional']['result'] = 'FAIL'
        self.assertEqual(qualification_exit_code(references), 1)
        references['dh_functional']['result'] = 'INCONCLUSIVE'
        self.assertEqual(qualification_exit_code(references), 2)
        self.assertEqual(qualification_exit_code({}), 2)
        self.assertEqual(qualification_exit_code({'dh_functional': {'result': 'PASS'}}), 2)

    def test_entity_saves_do_not_establish_terrain_generation(self):
        terrain = {
            'dimensions/minecraft/overworld/region/r.0.0.mca': {
                'size': 8192, 'chunks': [(0, 0)],
                'chunk_metadata': [{'Status': 'minecraft:full', 'xPos': 0, 'zPos': 0}],
            },
        }
        after = {
            **terrain,
            'dimensions/minecraft/overworld/entities/r.0.0.mca': {
                'size': 12288, 'chunks': [(0, 0)],
            },
        }
        self.assertEqual(generation_outcome(terrain, after), 'PASS')
        after['dimensions/minecraft/overworld/region/r.1.0.mca'] = {
            'size': 0, 'chunks': [], 'chunk_metadata': [],
        }
        # Empty terrain shells still require explicit pinned-source approval.
        self.assertEqual(generation_outcome(terrain, after), 'FAIL')
        manifest = {'mods': [{'id': 'distanthorizons', 'sha256': VERIFIED_DH_3_3_4_SHA256}]}
        self.assertEqual(generation_outcome(terrain, after, manifest), 'PASS')
        manifest['mods'][0]['sha256'] = 'unverified-build'
        self.assertEqual(generation_outcome(terrain, after, manifest), 'FAIL')
        manifest['mods'][0]['sha256'] = VERIFIED_DH_3_3_4_SHA256
        after['dimensions/minecraft/overworld/region/r.1.0.mca']['size'] = 8192
        self.assertEqual(generation_outcome(terrain, after, manifest), 'FAIL')

    def test_dh_pass_requires_real_nonexception_traffic(self):
        self.assertEqual(
            dh_outcome([]),
            'FAIL',
        )

        good = [{
            'monotonic_ns': 100,
            'type': 'FullDataSourceResponseMessage',
            'exception_type': '',
        }]

        self.assertEqual(
            dh_outcome(good),
            'PASS',
        )

        exception = [{
            'monotonic_ns': 100,
            'type': 'ExceptionMessage',
            'exception_type': 'IllegalStateException',
        }]

        self.assertEqual(
            dh_outcome(exception),
            'FAIL',
        )
        manifest = {'mods': [{'id': 'distanthorizons', 'sha256': VERIFIED_DH_3_3_4_SHA256}]}
        split = {'type': 'ExceptionMessage', 'exception_type': 'SectionRequiresSplittingException'}
        self.assertEqual(dh_outcome(good + [split], manifest), 'PASS')
        self.assertEqual(dh_outcome([split], manifest), 'FAIL')
        self.assertEqual(dh_outcome(good + [split]), 'FAIL')
        self.assertEqual(dh_outcome(good + exception, manifest), 'FAIL')
        manifest['mods'][0]['sha256'] = 'unverified'
        self.assertEqual(dh_outcome(good + [split], manifest), 'FAIL')

    def test_dh_telemetry_parser_rejects_malformed_or_regressing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dh-received.jsonl'

            path.write_text(
                json.dumps({
                    'monotonic_ns': 200,
                    'type': 'FirstMessage',
                    'exception_type': '',
                })
                + '\n'
                + json.dumps({
                    'monotonic_ns': 100,
                    'type': 'SecondMessage',
                    'exception_type': '',
                })
                + '\n'
            )

            with self.assertRaisesRegex(
                ValueError,
                'timestamps regressed',
            ):
                read_dh_messages(path)

            path.write_text(
                '{"monotonic_ns": 1, "type": "Message"}\n'
            )

            with self.assertRaisesRegex(
                ValueError,
                'schema',
            ):
                read_dh_messages(path)

    def test_generation_gate_rejects_new_chunk_occupancy(self):
        before = {
            'dimensions/minecraft/overworld/region/r.0.0.mca': {
                'size': 8192,
                'chunks': [(0, 0)],
                'chunk_metadata': [{
                    'Status': 'minecraft:full',
                    'xPos': 0,
                    'zPos': 0,
                }],
            },
        }

        unchanged = {
            'dimensions/minecraft/overworld/region/r.0.0.mca': {
                'size': 12288,
                'chunks': [(0, 0)],
                'chunk_metadata': [{
                    'Status': 'minecraft:full',
                    'xPos': 0,
                    'zPos': 0,
                }],
            },
        }

        changed = {
            'dimensions/minecraft/overworld/region/r.0.0.mca': {
                'size': 12288,
                'chunks': [(0, 0), (1, 0)],
                'chunk_metadata': [{
                    'Status': 'minecraft:full',
                    'xPos': 0,
                    'zPos': 0,
                }, {
                    'Status': 'minecraft:full',
                    'xPos': 1,
                    'zPos': 0,
                }],
            },
        }

        self.assertEqual(
            generation_outcome(before, unchanged),
            'PASS',
        )

        self.assertEqual(
            generation_outcome(before, changed),
            'FAIL',
        )

    def test_execute_writes_both_proofs_only_after_server_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'functional'
            state = {}

            before = {
                'dimensions/minecraft/overworld/region/r.0.0.mca': {
                    'size': 8192,
                    'chunks': [(0, 0)],
                    'chunk_metadata': [{
                        'Status': 'minecraft:full',
                        'xPos': 0,
                        'zPos': 0,
                    }],
                },
            }

            after = {
                'dimensions/minecraft/overworld/region/r.0.0.mca': {
                    'size': 12288,
                    'chunks': [(0, 0)],
                    'chunk_metadata': [{
                        'Status': 'minecraft:full',
                        'xPos': 0,
                        'zPos': 0,
                    }],
                },
            }

            class LifecycleLab:
                def __init__(self, manifest, path):
                    path.mkdir()

                    self.output = path
                    self.log = path / 'server.log'
                    self.log.write_text(
                        'server running\n'
                    )
                    self.server = (
                        path
                        / 'world-clone'
                        / 'survival'
                    )
                    self.pid = 111
                    self.active = False

                    state['lab'] = self

                def start(self):
                    self.active = True

                def stop(self):
                    if self.active:
                        with self.log.open('a') as stream:
                            stream.write(
                                'server stopped\n'
                            )

                        self.active = False

                def __enter__(self):
                    return self

                def __exit__(self, *exception):
                    self.stop()

            class LifecycleClient:
                def __init__(
                    self,
                    manifest,
                    client_output,
                    profile,
                    duration,
                    *,
                    fresh_cache=False,
                ):
                    self.output = client_output
                    self.pid = 222

                    self.assertions = (
                        profile,
                        duration,
                        fresh_cache,
                    )

                def __enter__(self):
                    self.output.mkdir()

                    (
                        self.output
                        / 'result.json'
                    ).write_text(
                        json.dumps({
                            'result': 'PASS',
                        })
                    )

                    (
                        self.output
                        / 'heartbeat.json'
                    ).write_text(
                        json.dumps({
                            'connected': True,
                            'elapsed_seconds': 45.0,
                        })
                    )

                    (
                        self.output
                        / 'launcher.log'
                    ).write_text(
                        'launcher finished\n'
                    )

                    (
                        self.output
                        / 'dh-received.jsonl'
                    ).write_text(
                        json.dumps({
                            'monotonic_ns': 100,
                            'type': 'FullDataSourceResponseMessage',
                            'exception_type': '',
                        })
                        + '\n'
                    )

                    return self

                def __exit__(self, *exception):
                    return None

            calls = []

            def fake_write_proof(
                manifest,
                gate,
                proof_path,
                evidence,
                result,
            ):
                lab = state['lab']

                self.assertFalse(
                    lab.active
                )
                self.assertIn(
                    'server stopped',
                    lab.log.read_text(),
                )
                self.assertIn(
                    (lab.log, 'log'),
                    evidence,
                )

                calls.append(
                    (gate, result)
                )

                proof_path.write_text('{}')

                return {
                    'result': result,
                    'evidence': str(proof_path),
                    'sha256': 'test-' + gate,
                }

            manifest = {
                'client': {},
                'baseline': {
                    'subvolume_uuid': 'test-baseline',
                },
            }

            with (
                patch(
                    'functional_dh.Lab',
                    LifecycleLab,
                ),
                patch(
                    'functional_dh.Client',
                    LifecycleClient,
                ),
                patch(
                    'functional_dh.exercise_dh_client',
                ),
                patch(
                    'functional_dh.region_occupancy',
                    side_effect=[before, after],
                ),
                patch(
                    'functional_dh.maintenance.enter',
                ),
                patch(
                    'functional_dh.write_proof',
                    side_effect=fake_write_proof,
                ),
            ):
                references = execute(
                    manifest,
                    output,
                )

            self.assertEqual(
                set(references),
                {
                    'dh_functional',
                    'no_unwanted_generation',
                },
            )

            self.assertEqual(
                calls,
                [
                    ('dh_functional', 'PASS'),
                    ('no_unwanted_generation', 'PASS'),
                ],
            )

            self.assertTrue(
                (
                    output
                    / 'dh-functional-reference.json'
                ).is_file()
            )

            self.assertFalse(
                (
                    output
                    / 'functional-acceptance.json'
                ).exists()
            )


if __name__ == '__main__':
    unittest.main()
