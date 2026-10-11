"""Enrich an exact-revision Nix candidate with immutable artifact/world identity."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from qualification_manifest import canonical_bytes, controlled_path, qualification_id, sha256


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def baseline_identity(base):
    controlled_path(base, Path('/persist'), existing=True)
    if not base.parent.name.startswith('minecraft-performance-lab-') or base.name != 'base':
        raise ValueError('baseline must be the private qualification base')
    metadata = command('btrfs', 'subvolume', 'show', str(base))
    uuid = re.search(r'^\s*UUID:\s*(\S+)\s*$', metadata, re.MULTILINE)
    if uuid is None or command('btrfs', 'property', 'get', str(base), 'ro') != 'ro=true':
        raise ValueError('baseline must be an identified readonly Btrfs subvolume')
    files = {}
    for path in sorted(base.rglob('*')):
        if path.is_file():
            files[str(path.relative_to(base))] = {'size': path.stat().st_size, 'sha256': sha256(path)}
    return {'path': str(base), 'subvolume_uuid': uuid.group(1), 'readonly': True,
            'filesystem_uuid': command('findmnt', '--noheadings', '--output', 'UUID', '--target', str(base)),
            'content_manifest_sha256': hashlib.sha256(canonical_bytes(files)).hexdigest(),
            'content_manifest': files}


def mod_inventory(directory, *, prism=False):
    inventory = []
    for path in sorted(Path(directory).iterdir()):
        if prism and path.name == '.index' and path.is_dir() and not path.is_symlink():
            continue
        if prism and (not path.name.endswith('.jar') or not path.is_file()):
            raise ValueError('unexpected disposable client mod entry')
        with zipfile.ZipFile(path) as archive:
            metadata = json.loads(archive.read('fabric.mod.json'))
        inventory.append({'id': metadata['id'], 'version': metadata['version'],
                          'filename': path.name, 'path': str(path.resolve()), 'sha256': sha256(path)})
    return inventory


def load_gate_mapping(repository, revision):
    mapping = 'scripts/minecraft-performance/gate-sources.json'
    committed = subprocess.check_output(['git', '-c', 'safe.directory=' + str(repository),
        '-C', str(repository), 'show', revision + ':' + mapping])
    if (repository / mapping).read_bytes() != committed:
        raise ValueError('gate mapping differs from frozen candidate')
    return json.loads(committed), hashlib.sha256(committed).hexdigest()


def generate(nix_manifest, base, repository, client_root=None, client_launcher=None):
    result = json.loads(nix_manifest.read_text())
    if not re.fullmatch('[0-9a-f]{40}', result['git_sha']):
        raise ValueError('Nix input must have an exact committed revision')
    for key in ('system_closure', 'minecraft_package', 'java_home', 'diagnostic_java_home',
                'mods_directory', 'pregen_mods_directory', 'pregen_dh_policy'):
        path = Path(result[key])
        if not path.is_relative_to('/nix/store') or not path.exists():
            raise ValueError('unrealized Nix candidate artifact: ' + key)
    for directory in result['qualification_tools_path'].split(':'):
        if not Path(directory).is_relative_to('/nix/store') or not Path(directory).is_dir():
            raise ValueError('unrealized qualification tool directory')
    package_identity = re.fullmatch(r'minecraft-server-(.+)-fabric-(.+)', result['minecraft_package_name'])
    if package_identity is None:
        raise ValueError('candidate package does not identify Minecraft and Fabric versions')
    result['minecraft_version'], result['fabric_loader_version'] = package_identity.groups()
    java = Path(result['java_home']) / 'bin/java'
    result['java'] = {'path': str(java), 'sha256': sha256(java),
                      'version': subprocess.check_output([str(java), '-version'], stderr=subprocess.STDOUT, text=True).strip()}
    wrapper = Path(result['minecraft_package']) / 'bin/minecraft-server'
    result['wrapper'] = {'path': str(wrapper), 'sha256': sha256(wrapper)}
    result['queue_agent'] = {'path': result['queue_agent_path'], 'sha256': sha256(result['queue_agent_path'])}
    result['mods'] = mod_inventory(result['mods_directory'])
    result['pregen_mods'] = mod_inventory(result['pregen_mods_directory'])
    pregen_policy = Path(result['pregen_dh_policy'])
    result['pregen_policy'] = {'path': str(pregen_policy), 'content': pregen_policy.read_text(),
                               'sha256': sha256(pregen_policy)}
    result['policies'] = {name: {'path': path, 'content': Path(path).read_text(), 'sha256': sha256(path)}
                          for name, path in result['policy_files'].items()}
    result['controlled_server_properties'] = {**result['server_properties'],
        'server-ip': '127.0.0.1', 'server-port': 25576, 'online-mode': False,
        'white-list': False, 'enforce-whitelist': False, 'management-server-enabled': False}
    result['controlled_server_properties'].pop('management-server-secret', None)
    result['baseline'] = baseline_identity(base)
    if client_root is not None:
        from client_identity import capture
        if client_launcher is None:
            raise ValueError('client launcher required with disposable client root')
        result['client'] = capture(client_root, client_launcher,
                                   Path(result['diagnostic_java_home']) / 'bin/java')
    gate_sources, result['gate_source_mapping_sha256'] = load_gate_mapping(repository, result['git_sha'])
    gates = {'dh_functional', 'non_dh_client', 'no_unwanted_generation', 'backup', 'restore',
             'identity_restart', 'post_chunky_catchup', 'no_unbounded_queues'}
    if set(gate_sources) != gates:
        raise ValueError('must freeze a test-source identity for every required gate')
    result['gate_test_sources'] = {}
    result['gate_source_files'] = {}
    result['tool_source_files'] = {}
    filenames = command('git', '-c', 'safe.directory=' + str(repository), '-C', str(repository),
                        'ls-tree', '-r', '--name-only', result['git_sha'],
                        'scripts/minecraft-performance').splitlines()
    for filename in filenames:
        committed = subprocess.check_output(['git', '-c', 'safe.directory=' + str(repository),
            '-C', str(repository), 'show', result['git_sha'] + ':' + filename])
        if (repository / filename).read_bytes() != committed:
            raise ValueError('qualification tool differs from frozen candidate: ' + filename)
        result['tool_source_files'][filename] = hashlib.sha256(committed).hexdigest()
    for gate, filenames in gate_sources.items():
        if not isinstance(filenames, list) or not filenames or len(filenames) != len(set(filenames)):
            raise ValueError('each gate needs a nonempty unique committed source list')
        # Every performance tool is a conservative shared dependency. The
        # committed mapping adds gate-specific sources outside that namespace.
        hashes = dict(result['tool_source_files'])
        for filename in filenames:
            path = Path(filename)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('test source must be relative to candidate repository')
            committed = subprocess.check_output(['git', '-c', 'safe.directory=' + str(repository),
                '-C', str(repository), 'show', result['git_sha'] + ':' + filename])
            if (repository / path).read_bytes() != committed:
                raise ValueError('test source differs from frozen candidate: ' + filename)
            hashes[filename] = hashlib.sha256(committed).hexdigest()
        result['gate_source_files'][gate] = hashes
        result['gate_test_sources'][gate] = hashlib.sha256(canonical_bytes(hashes)).hexdigest()
    if client_root is not None:
        from client_identity import verify_probe_build, generation_bounds
        verify_probe_build(result['client'])
        result['generation_bounds'] = generation_bounds(result['client'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nix-manifest', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--client-root', type=Path)
    parser.add_argument('--client-launcher', type=Path)
    args = parser.parse_args()
    manifest = generate(args.nix_manifest, args.baseline, args.repository.resolve(),
                        args.client_root, args.client_launcher)
    with args.output.open('xb') as stream:
        stream.write(canonical_bytes(manifest))
    args.output.chmod(0o444)
    print(qualification_id(manifest))
