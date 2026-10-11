from pathlib import Path
import tempfile
import unittest

from qualification_manifest import verify_proof
from qualification_proof import write_proof


class ProofReceiptTests(unittest.TestCase):
    def test_generated_proof_verifies_and_cannot_overwrite_a_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'runtime.json'
            source.write_text('{"observed": true}')
            manifest = {'git_sha': 'a' * 40, 'baseline': {'subvolume_uuid': 'baseline'},
                        'gate_test_sources': {'identity_restart': 'source-sha'}}
            reference = write_proof(manifest, 'identity_restart', root / 'proof.json', [(source, 'json')])
            self.assertEqual(verify_proof(reference, 'identity_restart', manifest), 'PASS')
            with self.assertRaises(FileExistsError):
                write_proof(manifest, 'identity_restart', root / 'proof.json', [(source, 'json')])
            source.write_text('{"observed": false}')
            self.assertEqual(verify_proof(reference, 'identity_restart', manifest), 'UNPROVEN')


if __name__ == '__main__':
    unittest.main()
