"""Build disposable probes from the pinned client's local Java/libraries."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def build(java_home, libraries, dh_jar, output):
    source = Path(__file__).parent / 'probe'
    output.mkdir(parents=True, exist_ok=True)
    minecraft = libraries / 'com/mojang/minecraft/26.3/minecraft-26.3-client.jar'
    if not minecraft.is_file():
        raise ValueError('Minecraft 26.3 client artifact missing')
    classpath = ':'.join(str(p) for p in sorted(libraries.rglob('*.jar'))) + ':' + str(dh_jar)
    variants = {
        'client-probe': (['ClientProbeMixin.java'], 'fabric.mod.json', 'performance-client.mixins.json'),
        'dh-probe': (['DhNetworkProbeMixin.java'], 'dh-fabric.mod.json', 'performance-dh.mixins.json'),
        'server-tick-probe': (['TickBuffer.java', 'ServerTickProbeMixin.java'], 'server-fabric.mod.json', 'performance-server.mixins.json'),
    }
    manifest = []
    with tempfile.TemporaryDirectory(prefix='minecraft-probes-') as directory:
        root = Path(directory)
        tests = root / 'tests'
        tests.mkdir()
        subprocess.run([str(java_home / 'bin/javac'), '-d', str(tests),
                        str(source / 'TickBuffer.java'), str(source / 'TickBufferTest.java')], check=True)
        subprocess.run([str(java_home / 'bin/java'), '-cp', str(tests),
                        'local.minecraft.performance.TickBufferTest'], check=True)
        for name, (files, metadata, mixin) in variants.items():
            classes = root / name
            classes.mkdir()
            subprocess.run([str(java_home / 'bin/javac'), '-proc:none', '-cp', classpath,
                            '-d', str(classes), *(str(source / f) for f in files)], check=True)
            (classes / 'fabric.mod.json').write_bytes((source / metadata).read_bytes())
            (classes / mixin).write_bytes((source / mixin).read_bytes())
            artifact = output / (name + '.jar')
            subprocess.run([str(java_home / 'bin/jar'), '--create', '--date=2026-01-01T00:00:00Z',
                            '--file', str(artifact), '-C', str(classes), '.'], check=True)
            manifest.append({'name': name, 'size': artifact.stat().st_size,
                             'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()})
    (output / 'probe-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--libraries', type=Path, required=True)
    parser.add_argument('--dh-jar', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.java_home, args.libraries, args.dh_jar, args.output), indent=2))
