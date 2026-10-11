import json
from pathlib import Path
import tempfile
import unittest

from qualification_manifest import canonical_bytes, controlled_path, qualification_id, sha256, verify_proof


class ManifestProofTests(unittest.TestCase):
    def test_exact_identity_and_artifact_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / 'runtime.log'
            artifact.write_text('verified runtime observation\n')
            manifest = {'git_sha': 'a' * 40, 'baseline': {'subvolume_uuid': 'baseline'},
                        'gate_test_sources': {'restore': 'source-hash'}}
            identity = qualification_id(manifest)
            proof = {'schema': 1, 'result': 'PASS', 'gate': 'restore',
                     'git_sha': manifest['git_sha'], 'qualification_id': identity,
                     'manifest_sha256': identity, 'baseline_uuid': 'baseline',
                     'test_source_sha256': 'source-hash',
                     'evidence': [{'path': str(artifact), 'sha256': sha256(artifact), 'type': 'log'}]}
            path = root / 'proof.json'
            def check(value, candidate=manifest, gate='restore'):
                path.write_bytes(canonical_bytes(value))
                return verify_proof({'evidence': str(path), 'sha256': sha256(path)}, gate, candidate)
            self.assertEqual(check(proof), 'PASS')
            for key in ('schema', 'git_sha', 'qualification_id', 'manifest_sha256',
                        'baseline_uuid', 'test_source_sha256', 'gate'):
                self.assertEqual(check({**proof, key: 'stale'}), 'UNPROVEN', key)
            self.assertEqual(check({**proof, 'evidence': []}), 'UNPROVEN')
            self.assertEqual(check(proof, gate='backup'), 'UNPROVEN')
            changed = {**manifest, 'jvm_flags': ['-Xmx10G']}
            self.assertEqual(check(proof, candidate=changed), 'UNPROVEN')
            artifact.write_text('modified after proof')
            self.assertEqual(check(proof), 'UNPROVEN')

    def test_root_path_aliases_and_existing_outputs_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'target'
            target.mkdir()
            alias = root / 'alias'
            alias.symlink_to(target)
            self.assertEqual(controlled_path(root / 'new', root), root / 'new')
            for path in (alias / 'new', root / 'target' / '..' / 'new', target, root, Path('/etc/new')):
                with self.assertRaises(ValueError):
                    controlled_path(path, root)


if __name__ == '__main__':
    unittest.main()
