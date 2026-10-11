"""Inspect immutable copies of closed qualification DH databases."""

import hashlib
from pathlib import Path
import shutil
import sqlite3



def _terrain_fingerprints(connection, requested_sections):
    fingerprint = hashlib.sha256()
    section_fingerprints = {}
    for row in connection.execute('SELECT DetailLevel, PosX, PosZ, DataChecksum, Data FROM FullData ORDER BY DetailLevel, PosX, PosZ'):
        section = hashlib.sha256()
        for value in row:
            encoded = value if isinstance(value, bytes) else str(value).encode()
            fingerprint.update(len(encoded).to_bytes(8, 'big'))
            fingerprint.update(encoded)
            section.update(len(encoded).to_bytes(8, 'big'))
            section.update(encoded)
        if tuple(row[:3]) in requested_sections:
            section_fingerprints[','.join(map(str, row[:3]))] = section.hexdigest()
    return fingerprint.hexdigest(), section_fingerprints

def inspect_closed_database(source, destination, *, owner_stopped, require_useful=True, requested_sections=()):
    if owner_stopped is not True:
        raise RuntimeError('DH database owner must be stopped before inspection')
    source, destination = Path(source), Path(destination)
    if source.is_symlink() or source.resolve() != source or not source.is_file():
        raise RuntimeError('unsafe DH database source')
    if destination.exists() or destination.is_symlink() or destination.resolve() != destination:
        raise RuntimeError('DH database copy destination must be new and canonical')
    for suffix in ('-wal', '-shm'):
        sidecar = Path(str(destination) + suffix)
        if sidecar.exists() or sidecar.is_symlink():
            raise RuntimeError('DH copy sidecar destination already exists')
    # Keep any final WAL beside the copy; SQLite reads only the private copy.
    shutil.copyfile(source, destination)
    for suffix in ('-wal', '-shm'):
        sidecar = Path(str(source) + suffix)
        if sidecar.exists():
            if sidecar.is_symlink() or sidecar.resolve() != sidecar:
                raise RuntimeError('unsafe DH database sidecar')
            shutil.copyfile(sidecar, Path(str(destination) + suffix))
    connection = sqlite3.connect(destination)
    try:
        integrity = [row[0] for row in connection.execute('PRAGMA integrity_check')]
        if integrity != ['ok']:
            raise RuntimeError('DH database integrity check failed')
        schema = connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        # Empty schema or rows without data cannot qualify useful cached terrain.
        useful = connection.execute('SELECT COUNT(*) FROM FullData WHERE length(Data) > 0').fetchone()[0]
        if require_useful and useful <= 0:
            raise RuntimeError('DH database contains no useful FullData rows')
        fingerprint, section_fingerprints = _terrain_fingerprints(connection, requested_sections)
        checkpoint = connection.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
        if checkpoint[0] != 0 or checkpoint[1] != checkpoint[2]:
            raise RuntimeError('DH evidence checkpoint did not complete')
        if connection.execute('PRAGMA journal_mode=DELETE').fetchone()[0] != 'delete':
            raise RuntimeError('DH evidence did not become self-contained')
    finally:
        connection.close()
    for suffix in ('-wal', '-shm'):
        Path(str(destination) + suffix).unlink(missing_ok=True)
    # Immutable mode ignores sidecars: independently prove the main file alone
    # contains the same healthy useful-data observation before hashing it.
    standalone = sqlite3.connect(destination.as_uri() + '?immutable=1', uri=True)
    try:
        if standalone.execute('PRAGMA integrity_check').fetchall() != [('ok',)] or standalone.execute('SELECT COUNT(*) FROM FullData WHERE length(Data) > 0').fetchone()[0] != useful or _terrain_fingerprints(standalone, requested_sections) != (fingerprint, section_fingerprints):
            raise RuntimeError('standalone DH evidence differs from inspected content')
    finally:
        standalone.close()
    destination.chmod(0o400)
    with destination.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'source': str(source), 'copy': str(destination), 'integrity': 'ok', 'size': destination.stat().st_size,
            'sha256': digest,
            'schema': schema, 'useful_full_data_rows': useful,
            'full_data_fingerprint': fingerprint,
            'requested_section_fingerprints': section_fingerprints}


def inspect_closed_cache(root, output, *, owner_stopped, requested_sections=()):
    root, output = Path(root), Path(output)
    if root.is_symlink() or root.resolve() != root or not root.is_dir():
        raise RuntimeError('fresh DH cache is missing or unsafe')
    databases = sorted(root.rglob('DistantHorizons.sqlite'))
    if not databases:
        raise RuntimeError('fresh DH cache has no database')
    return [inspect_closed_database(source, output / f'dh-database-{index}.sqlite',
                                    owner_stopped=owner_stopped, requested_sections=requested_sections)
            for index, source in enumerate(databases)]
