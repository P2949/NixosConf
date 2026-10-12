import copy
import subprocess
import json
from pathlib import Path
import tempfile
import unittest

from qualification_manifest import canonical_bytes, controlled_path, qualification_id, sha256, verify_proof, validate_candidate, reconstruct_provenance, REQUIRED_GATES


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
            for outcome in ('FAIL', 'INCONCLUSIVE'):
                self.assertEqual(check({**proof, 'result': outcome}), outcome)
                self.assertEqual(check({**proof, 'result': outcome, 'git_sha': 'stale'}), 'UNPROVEN')
            for key in ('schema', 'git_sha', 'qualification_id', 'manifest_sha256',
                        'baseline_uuid', 'test_source_sha256', 'gate'):
                self.assertEqual(check({**proof, key: 'stale'}), 'UNPROVEN', key)
            self.assertEqual(check({**proof, 'evidence': []}), 'UNPROVEN')
            self.assertEqual(check(proof, gate='backup'), 'UNPROVEN')
            changed = {**manifest, 'jvm_flags': ['-Xmx10G']}
            self.assertEqual(check(proof, candidate=changed), 'UNPROVEN')
            artifact.write_text('modified after proof')
            self.assertEqual(check(proof), 'UNPROVEN')
            self.assertEqual(check({**proof, 'result': 'FAIL'}), 'UNPROVEN')

    def test_committed_provenance_and_all_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = root / 'scripts/minecraft-performance'
            tools.mkdir(parents=True)
            source = root / 'external-identity.py'
            source.write_text('frozen external implementation')
            (tools / 'gate-sources.json').write_bytes(canonical_bytes(
                {gate: [source.name] for gate in REQUIRED_GATES}))
            (tools / 'tool.py').write_text('frozen tool')
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args],
                                               stderr=subprocess.DEVNULL, text=True).strip()
            git('init')
            git('add', '.')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                'commit', '-m', 'fixture')
            revision = git('rev-parse', 'HEAD')
            artifact = root / 'artifact'
            artifact.write_bytes(b'fixed')
            entry = {'path': str(artifact), 'sha256': sha256(artifact)}
            manifest = {'schema': 1, 'git_sha': revision, 'wrapper': entry,
                        'java': entry, 'pregen_policy': entry, 'queue_agent': entry,
                        'mods': [], 'pregen_mods': [], 'policies': {},
                        **reconstruct_provenance(root, revision)}
            validate_candidate(manifest, root)
            for field in ('gate_test_sources', 'gate_source_files', 'tool_source_files'):
                for operation in ('missing', 'extra', 'changed'):
                    changed = copy.deepcopy(manifest)
                    value = changed[field]
                    key = next(iter(value))
                    if operation == 'missing':
                        del value[key]
                    elif operation == 'extra':
                        value['foreign'] = value[key]
                    else:
                        value[key] = 'arbitrary'
                    with self.subTest(field=field, operation=operation), self.assertRaises(ValueError):
                        validate_candidate(changed, root)
            for field, value in (('gate_source_mapping_sha256', 'arbitrary'),
                                 ('git_sha', 'a' * 40), ('git_sha', True)):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    validate_candidate({**manifest, field: value}, root)
            source.write_text('new committed external implementation')
            git('add', source.name)
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                'commit', '-m', 'changed source')
            with self.assertRaises(ValueError):
                validate_candidate(manifest, root)
            with self.assertRaises(ValueError):
                validate_candidate({**manifest, 'git_sha': git('rev-parse', 'HEAD')}, root)

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
