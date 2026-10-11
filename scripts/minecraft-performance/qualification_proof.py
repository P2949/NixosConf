"""Write qualification-bound receipts with concrete, hashed evidence."""

from qualification_manifest import canonical_bytes, qualification_id, sha256


def write_proof(manifest, gate, output, evidence, result='PASS'):
    if result not in ('PASS', 'FAIL', 'INCONCLUSIVE') or not evidence:
        raise ValueError('proof needs a permitted outcome and nonempty evidence')
    identity = qualification_id(manifest)
    proof = {'schema': 1, 'result': result, 'gate': gate,
             'qualification_id': identity, 'manifest_sha256': identity,
             'git_sha': manifest['git_sha'], 'baseline_uuid': manifest['baseline']['subvolume_uuid'],
             'test_source_sha256': manifest['gate_test_sources'][gate],
             'evidence': [{'path': str(path.resolve()), 'sha256': sha256(path), 'type': kind}
                          for path, kind in evidence]}
    with output.open('xb') as stream:
        stream.write(canonical_bytes(proof))
    output.chmod(0o400)
    return {'result': result, 'evidence': str(output), 'sha256': sha256(output)}
