from pathlib import Path
import tempfile
import unittest

from assemble_functional_acceptance import REQUIRED, assemble, verify_bundle, read_input
from qualification_proof import write_proof


class FunctionalAggregationTests(unittest.TestCase):
    def test_duplicate_gates_in_one_json_input_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text('{"restore":{},"restore":{}}')
            with self.assertRaises(ValueError):
                read_input(path)

    def fixture(self, root, result='PASS'):
        manifest = {'git_sha': 'a' * 40, 'baseline': {'subvolume_uuid': 'fixed-world'},
                    'gate_test_sources': {gate: 'frozen-source-' + gate for gate in REQUIRED}}
        evidence = root / 'evidence.log'
        evidence.write_text('machine-readable runtime evidence fixture')
        references = {gate: write_proof(manifest, gate, root / (gate + '.json'),
                      [(evidence, 'log')], result if gate == 'restore' else 'PASS') for gate in REQUIRED}
        return manifest, references

    def test_complete_bundle_preserves_authentic_outcomes(self):
        for outcome in ('PASS', 'FAIL', 'INCONCLUSIVE'):
            with tempfile.TemporaryDirectory() as directory:
                manifest, refs = self.fixture(Path(directory), outcome)
                bundle = assemble(manifest, [refs])
                self.assertEqual(bundle['outcomes']['restore'], outcome)
                self.assertEqual(verify_bundle(bundle, manifest), bundle['outcomes'])

    def test_duplicate_missing_mixed_and_tampered_bundles_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, refs = self.fixture(root)
            for inputs in ([refs, {'restore': refs['restore']}],
                           [{key: value for key, value in refs.items() if key != 'restore'}]):
                with self.assertRaises(ValueError):
                    assemble(manifest, inputs)
            with self.assertRaises(ValueError):
                assemble({**manifest, 'git_sha': 'b' * 40}, [refs])
            bundle = assemble(manifest, [refs])
            bundle['outcomes']['restore'] = 'FAIL'
            self.assertTrue(all(value == 'UNPROVEN' for value in verify_bundle(bundle, manifest).values()))
            (root / 'evidence.log').write_text('changed')
            with self.assertRaises(ValueError):
                assemble(manifest, [refs])


if __name__ == '__main__':
    unittest.main()
