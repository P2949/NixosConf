"""Immutable qualification identity and fail-closed proof verification."""

import hashlib
import json
import re
import subprocess
from pathlib import Path


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def qualification_id(manifest):
    return hashlib.sha256(canonical_bytes(manifest)).hexdigest()


REQUIRED_GATES = ('dh_functional', 'non_dh_client', 'no_unwanted_generation',
                  'backup', 'restore', 'identity_restart', 'post_chunky_catchup',
                  'no_unbounded_queues')
PROVENANCE_FIELDS = ('gate_source_mapping_sha256', 'tool_source_files',
                     'gate_source_files', 'gate_test_sources')


def reconstruct_provenance(repository, revision):
    """Derive complete gate identity from Git blobs and check the working copy."""
    repository = Path(repository)
    if not isinstance(revision, str) or not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('qualification source requires an exact Git revision')
    git = ['git', '-c', 'safe.directory=' + str(repository), '-C', str(repository)]

    def blob(filename):
        path = Path(filename)
        if path.is_absolute() or '..' in path.parts or str(path) != filename:
            raise ValueError('noncanonical qualification source path')
        try:
            committed = subprocess.check_output(git + ['show', revision + ':' + filename])
            if (repository / path).read_bytes() != committed:
                raise ValueError('qualification source differs from frozen candidate: ' + filename)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError('unavailable committed qualification source: ' + filename) from exc
        return committed

    mapping_bytes = blob('scripts/minecraft-performance/gate-sources.json')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate gate mapping key')
            result[key] = value
        return result
    mapping = json.loads(mapping_bytes, object_pairs_hook=unique)
    if not isinstance(mapping, dict) or set(mapping) != set(REQUIRED_GATES):
        raise ValueError('exact required qualification gate set required')
    try:
        filenames = subprocess.check_output(git + ['ls-tree', '-r', '--name-only',
            revision, 'scripts/minecraft-performance'], text=True).splitlines()
    except subprocess.CalledProcessError as exc:
        raise ValueError('unavailable qualification revision') from exc
    tools = {name: hashlib.sha256(blob(name)).hexdigest() for name in filenames}
    sources, digests = {}, {}
    for gate, external in mapping.items():
        if (not isinstance(external, list) or not external
                or any(not isinstance(name, str) for name in external)
                or len(external) != len(set(external))):
            raise ValueError('nonempty unique committed gate sources required')
        hashes = dict(tools)
        for name in external:
            hashes[name] = hashlib.sha256(blob(name)).hexdigest()
        sources[gate] = hashes
        digests[gate] = hashlib.sha256(canonical_bytes(hashes)).hexdigest()
    return dict(gate_source_mapping_sha256=hashlib.sha256(mapping_bytes).hexdigest(),
                tool_source_files=tools, gate_source_files=sources, gate_test_sources=digests)


def validate_candidate(manifest, repository):
    if manifest.get('schema') != 1:
        raise ValueError('unsupported qualification manifest')
    artifacts = [manifest['wrapper'], manifest['java'], manifest['pregen_policy'], manifest['queue_agent'],
                 *manifest['mods'], *manifest['pregen_mods'], *manifest['policies'].values()]
    if 'dh_pregen_policy' in manifest:
        artifacts.extend([manifest['dh_pregen_policy'], *manifest['dh_pregen_mods']])
    if 'client' in manifest:
        client = manifest['client']
        artifacts.extend([client['java'], client['launcher'], *client['libraries']])
        for profile in client['profiles'].values():
            artifacts.extend([profile['pack'], *profile['mods']])
    for artifact in artifacts:
        if sha256(artifact['path']) != artifact['sha256']:
            raise ValueError('candidate artifact hash mismatch')
        if 'content' in artifact and hashlib.sha256(artifact['content'].encode()).hexdigest() != artifact['sha256']:
            raise ValueError('candidate policy content mismatch')
    expected = reconstruct_provenance(repository, manifest.get('git_sha'))
    for field in PROVENANCE_FIELDS:
        if manifest.get(field) != expected[field]:
            raise ValueError('qualification derived provenance mismatch: ' + field)


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
            'schema': 1, 'gate': gate_name,
            'qualification_id': identity, 'manifest_sha256': identity,
            'git_sha': manifest['git_sha'],
            'test_source_sha256': manifest['gate_test_sources'][gate_name],
            'baseline_uuid': manifest['baseline']['subvolume_uuid'],
        }
        if any(proof.get(key) != value for key, value in expected.items()):
            return 'UNPROVEN'
        outcome = proof.get('result')
        if outcome not in ('PASS', 'FAIL', 'INCONCLUSIVE'):
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
        return outcome
    except (OSError, ValueError, KeyError, TypeError):
        return 'UNPROVEN'
