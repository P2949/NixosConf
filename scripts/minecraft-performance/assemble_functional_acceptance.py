"""Assemble eight authentic same-candidate functional proofs; never invent outcomes."""

import argparse
import json
from pathlib import Path

from qualification_manifest import canonical_bytes, qualification_id, verify_proof

REQUIRED = ('dh_functional', 'non_dh_client', 'no_unwanted_generation', 'backup', 'restore',
            'identity_restart', 'post_chunky_catchup', 'no_unbounded_queues')


def read_input(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key/gate: ' + key)
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def assemble(manifest, inputs):
    references = {}
    outcomes = {}
    for entries in inputs:
        for gate, reference in entries.items():
            if gate not in REQUIRED or gate in references:
                raise ValueError('unknown or duplicate functional gate: ' + gate)
            outcome = verify_proof(reference, gate, manifest)
            if outcome == 'UNPROVEN':
                raise ValueError('unauthenticated or mixed-candidate proof: ' + gate)
            references[gate] = reference
            outcomes[gate] = outcome
    if set(references) != set(REQUIRED):
        raise ValueError('complete eight-gate proof set required')
    return {'schema': 1, 'qualification_id': qualification_id(manifest),
            'git_sha': manifest['git_sha'], 'gates': references, 'outcomes': outcomes}


def verify_bundle(bundle, manifest):
    try:
        expected = assemble(manifest, [bundle['gates']])
        if bundle != expected:
            raise ValueError('functional bundle metadata/outcomes differ')
        return expected['outcomes']
    except (ValueError, KeyError, TypeError):
        return {gate: 'UNPROVEN' for gate in REQUIRED}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--input', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = assemble(read_input(args.manifest), [read_input(path) for path in args.input])
    with args.output.open('xb') as stream:
        stream.write(canonical_bytes(result))
    args.output.chmod(0o444)
