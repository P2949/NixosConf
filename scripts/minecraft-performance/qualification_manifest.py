"""Immutable qualification identity and fail-closed proof verification."""

import hashlib
import json
from pathlib import Path


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def qualification_id(manifest):
    return hashlib.sha256(canonical_bytes(manifest)).hexdigest()


def controlled_path(path, namespace, *, existing=False):
    """Reject aliases before any privileged mutation, including symlink parents."""
    path = Path(path)
    namespace = Path(namespace)
    if not path.is_absolute() or '..' in path.parts or path != path.resolve():
        raise ValueError('noncanonical controlled path')
    if not path.is_relative_to(namespace) or path == namespace:
        raise ValueError('controlled path outside private namespace')
    if existing != path.exists():
        raise ValueError('unexpected controlled path existence')
    return path


def verify_proof(reference, gate_name, manifest):
    """A PASS string or an unrelated correctly hashed PASS is never sufficient."""
    try:
        if not isinstance(reference, dict) or manifest is None:
            return 'UNPROVEN'
        path = Path(reference['evidence'])
        if not path.is_absolute() or path != path.resolve() or sha256(path) != reference['sha256']:
            return 'UNPROVEN'
        proof = json.loads(path.read_text())
        identity = qualification_id(manifest)
        expected = {
            'schema': 1, 'result': 'PASS', 'gate': gate_name,
            'qualification_id': identity, 'manifest_sha256': identity,
            'git_sha': manifest['git_sha'],
            'test_source_sha256': manifest['gate_test_sources'][gate_name],
            'baseline_uuid': manifest['baseline']['subvolume_uuid'],
        }
        if any(proof.get(key) != value for key, value in expected.items()):
            return 'UNPROVEN'
        evidence = proof.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            return 'UNPROVEN'
        for item in evidence:
            artifact = Path(item['path'])
            if item['type'] not in ('json', 'log', 'sqlite', 'jfr', 'binary'):
                return 'UNPROVEN'
            if not artifact.is_absolute() or artifact != artifact.resolve() or sha256(artifact) != item['sha256']:
                return 'UNPROVEN'
        return 'PASS'
    except (OSError, ValueError, KeyError, TypeError):
        return 'UNPROVEN'
