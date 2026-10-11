"""Freeze disposable Prism inputs without reading account or credential files."""

import configparser
import hashlib
from pathlib import Path
import tempfile
import subprocess
import re

from generate_candidate_manifest import mod_inventory
from qualification_manifest import canonical_bytes, controlled_path, sha256

VOLATILE = {'lastLaunchTime', 'lastTimePlayed', 'totalTimePlayed', 'name', 'uuid'}
CONFIGS = ('options.txt', 'config/DistantHorizons.toml')


def general_settings(path):
    config = configparser.ConfigParser(interpolation=None, strict=True)
    config.optionxform = str
    config.read_string(path.read_text())
    return {key: value for key, value in config['General'].items() if key not in VOLATILE}


def capture(root, launcher, java):
    root = controlled_path(root, Path('/persist'), existing=True)
    if root.parent != Path('/persist') or not root.name.startswith('minecraft-performance-client-'):
        raise ValueError('client root must be the private disposable Prism namespace')
    launcher_settings = general_settings(root / 'prismlauncher.cfg')
    if launcher_settings.get('JavaPath') != str(java):
        raise ValueError('Prism Java differs from frozen client Java')
    libraries = (root / 'libraries').resolve()
    result = {'root': str(root), 'profiles': {}, 'java': {'path': str(java), 'sha256': sha256(java)},
              'libraries': [{'path': str(path), 'sha256': sha256(path)}
                            for path in sorted(libraries.rglob('*.jar'))],
              'launcher': {'path': str(launcher), 'sha256': sha256(launcher)}}
    for name in ('dh-clean', 'no-dh'):
        instance = controlled_path(root / 'instances' / name, root, existing=True)
        game = controlled_path(instance / 'minecraft', root, existing=True)
        files = {}
        for filename in CONFIGS:
            path = controlled_path(game / filename, root, existing=(game / filename).exists())
            if path.exists():
                files[filename] = {'content': path.read_text(), 'sha256': sha256(path)}
        pack = controlled_path(instance / 'mmc-pack.json', root, existing=True)
        settings = general_settings(instance / 'instance.cfg')
        if (settings.get('JvmArgs') != '-XX:+UseZGC' or settings.get('MaxMemAlloc') != '8192'
                or settings.get('MinMemAlloc') != '1024'
                or settings.get('OverrideJavaArgs') != 'true' or settings.get('OverrideMemory') != 'true'
                or settings.get('OverrideJava', 'false') != 'false'):
            raise ValueError('qualification client requires fixed 8 GiB ZGC configuration')
        inventory = mod_inventory(game / 'mods', prism=True)
        ids = {mod['id'] for mod in inventory}
        if 'local_performance_client_probe' not in ids:
            raise ValueError('client frame probe missing')
        has_dh = any(mod['id'] == 'distanthorizons' for mod in inventory)
        if has_dh != (name == 'dh-clean'):
            raise ValueError('DH/non-DH client inventory mismatch')
        if ('local_performance_dh_probe' in ids) != has_dh:
            raise ValueError('functional packet probe inventory mismatch')
        result['profiles'][name] = {'settings': settings, 'files': files,
            'pack': {'path': str(pack), 'sha256': sha256(pack)}, 'mods': inventory}
    return result


def verify(identity, name):
    root = controlled_path(identity['root'], Path('/persist'), existing=True)
    instance = controlled_path(root / 'instances' / name, root, existing=True)
    profile = identity['profiles'][name]
    if general_settings(root / 'prismlauncher.cfg').get('JavaPath') != identity['java']['path']:
        raise ValueError('Prism Java changed')
    if general_settings(instance / 'instance.cfg') != profile['settings']:
        raise ValueError('client Java/performance settings changed')
    artifacts = [identity['java'], identity['launcher'], profile['pack'], *profile['mods'], *identity['libraries']]
    if any(sha256(item['path']) != item['sha256'] for item in artifacts):
        raise ValueError('client artifact changed')
    actual = mod_inventory(instance / 'minecraft/mods', prism=True)
    if actual != profile['mods']:
        raise ValueError('client inventory changed')
    for filename, entry in profile['files'].items():
        path = controlled_path(instance / 'minecraft' / filename, root, existing=True)
        if sha256(path) != entry['sha256']:
            raise ValueError('client options/configuration changed')
    return instance


def verify_probe_build(identity):
    """Reject an old probe JAR even when its unrelated source hash is current."""
    from build_probes import build
    dh = next(mod for mod in identity['profiles']['dh-clean']['mods'] if mod['id'] == 'distanthorizons')
    with tempfile.TemporaryDirectory(prefix='minecraft-client-probe-identity-') as directory:
        expected = {entry['name']: entry['sha256'] for entry in build(
            Path(identity['java']['path']).parent.parent,
            (Path(identity['root']) / 'libraries').resolve(), Path(dh['path']), Path(directory))}
    for profile in identity['profiles'].values():
        for mod in profile['mods']:
            name = {'local_performance_client_probe': 'client-probe',
                    'local_performance_dh_probe': 'dh-probe'}.get(mod['id'])
            if name and mod['sha256'] != expected[name]:
                raise ValueError('client probe binary differs from frozen source build')


def generation_bounds(identity):
    source = Path(__file__).parent / 'probe/GenerationBounds.java'
    classpath = ':'.join(entry['path'] for entry in identity['libraries'])
    with tempfile.TemporaryDirectory(prefix='minecraft-generation-bounds-') as directory:
        output = subprocess.check_output([identity['java']['path'], '-cp', classpath, str(source)],
                                         cwd=directory, text=True, stderr=subprocess.DEVNULL, timeout=90)
    bounds = {name: int(radius) for name, radius in re.findall(
        r'GENERATION_BOUND (minecraft:[a-z_]+)=(\d+)', output)}
    if bounds.get('minecraft:full') != 0 or len(bounds) != 10:
        raise ValueError('unknown pinned Minecraft generation dependency schema')
    return {'dependency_radius_chunks': bounds, 'source_sha256': sha256(source),
            'classpath_sha256': hashlib.sha256(canonical_bytes(identity['libraries'])).hexdigest()}
