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
