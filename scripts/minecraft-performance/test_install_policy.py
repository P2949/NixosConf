import tempfile
import unittest
from pathlib import Path
from install_policy import install


class PolicyTests(unittest.TestCase):
    def test_readonly_source_becomes_writable(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            destination = Path(directory) / 'destination'
            source.write_text('[server]\nsynchronizeOnLoad=true\n')
            source.chmod(0o444)
            install(source, destination)
            self.assertEqual(destination.read_bytes(), source.read_bytes())
            self.assertEqual(destination.stat().st_mode & 0o777, 0o660)
            self.assertEqual(destination.stat().st_uid, destination.parent.stat().st_uid)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            source.write_text('test')
            destination = Path(directory) / 'destination'
            destination.symlink_to(source)
            with self.assertRaises(ValueError):
                install(source, destination)


if __name__ == '__main__':
    unittest.main()
