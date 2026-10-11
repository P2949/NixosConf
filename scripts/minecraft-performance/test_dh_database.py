from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from dh_database import inspect_closed_database


class DatabaseTests(unittest.TestCase):
    def test_requires_closed_owner_and_useful_healthy_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sqlite'
            with closing(sqlite3.connect(source)) as connection:
                connection.execute('CREATE TABLE FullData(DetailLevel, PosX, PosZ, DataChecksum, Data)')
            with self.assertRaisesRegex(RuntimeError, 'owner must be stopped'):
                inspect_closed_database(source, root / 'live.sqlite', owner_stopped=False)
            with self.assertRaisesRegex(RuntimeError, 'no useful'):
                inspect_closed_database(source, root / 'empty.sqlite', owner_stopped=True)
            with closing(sqlite3.connect(source)) as connection:
                connection.execute('INSERT INTO FullData VALUES(0,1,2,3,?)', (b'useful terrain',))
                connection.commit()
            result = inspect_closed_database(source, root / 'copy.sqlite', owner_stopped=True)
            self.assertEqual(result['integrity'], 'ok')
            self.assertEqual(result['useful_full_data_rows'], 1)
            self.assertEqual(len(result['full_data_fingerprint']), 64)
            self.assertTrue(result['schema'])

    def test_corrupt_database_cannot_qualify(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sqlite'
            source.write_bytes(b'corrupt')
            with self.assertRaises(sqlite3.DatabaseError):
                inspect_closed_database(source, root / 'copy.sqlite', owner_stopped=True)

    def test_section_fingerprint_ignores_metadata_and_detects_terrain_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sqlite'
            with closing(sqlite3.connect(source)) as connection:
                connection.execute('CREATE TABLE FullData(DetailLevel, PosX, PosZ, DataChecksum, Data, Timestamp)')
                connection.execute('INSERT INTO FullData VALUES(0,-5,0,7,?,0)', (b'terrain',))
                connection.commit()
            def inspect(name):
                return inspect_closed_database(source, root / name, owner_stopped=True,
                                               requested_sections=((0, -5, 0),))
            before = inspect('before.sqlite')
            with closing(sqlite3.connect(source)) as connection:
                connection.execute('UPDATE FullData SET Timestamp=1')
                connection.commit()
            metadata = inspect('metadata.sqlite')
            self.assertNotEqual(before['sha256'], metadata['sha256'])
            self.assertEqual(before['requested_section_fingerprints'], metadata['requested_section_fingerprints'])
            with closing(sqlite3.connect(source)) as connection:
                connection.execute('UPDATE FullData SET Data=?, DataChecksum=8', (b'gold landmark',))
                connection.commit()
            changed = inspect('changed.sqlite')
            self.assertNotEqual(before['requested_section_fingerprints'], changed['requested_section_fingerprints'])

    def test_wal_rows_become_self_contained_read_only_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / 'fixture-builder.sqlite'
            frozen = root / 'closed-source.sqlite'
            with closing(sqlite3.connect(live)) as connection:
                connection.execute('PRAGMA journal_mode=WAL')
                connection.execute('PRAGMA wal_autocheckpoint=0')
                connection.execute('CREATE TABLE FullData(DetailLevel, PosX, PosZ, DataChecksum, Data)')
                connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                connection.execute('INSERT INTO FullData VALUES(0,-5,0,7,?)', (b'committed WAL terrain',))
                connection.commit()
                # Freeze bytes, then close the fixture builder. The inspector's
                # source has no live SQLite owner and contains an uncheckpointed WAL.
                frozen.write_bytes(live.read_bytes())
                Path(str(frozen) + '-wal').write_bytes(Path(str(live) + '-wal').read_bytes())
            copy = root / 'copy.sqlite'
            result = inspect_closed_database(frozen, copy, owner_stopped=True)
            self.assertEqual(result['useful_full_data_rows'], 1)
            self.assertFalse(Path(str(copy) + '-wal').exists())
            self.assertFalse(Path(str(copy) + '-shm').exists())
            with closing(sqlite3.connect(copy.as_uri() + '?immutable=1', uri=True)) as connection:
                self.assertEqual(connection.execute('PRAGMA integrity_check').fetchall(), [('ok',)])
                self.assertEqual(connection.execute('SELECT Data FROM FullData').fetchone()[0], b'committed WAL terrain')
            self.assertEqual(copy.stat().st_mode & 0o777, 0o400)

    def test_existing_destination_sidecar_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.sqlite'
            source.write_bytes(b'source')
            sidecar = root / 'copy.sqlite-wal'
            sidecar.write_bytes(b'foreign')
            with self.assertRaisesRegex(RuntimeError, 'sidecar destination already exists'):
                inspect_closed_database(source, root / 'copy.sqlite', owner_stopped=True)
            self.assertEqual(sidecar.read_bytes(), b'foreign')
            self.assertFalse((root / 'copy.sqlite').exists())
