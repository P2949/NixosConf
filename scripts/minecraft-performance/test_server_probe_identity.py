from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from generate_candidate_manifest import freeze_server_tick_probe
from qualification_manifest import sha256


class ServerProbeIdentityTests(unittest.TestCase):
    def test_verified_rebuilt_binary_required(self):
        with tempfile.TemporaryDirectory() as directory:
            probe = Path(directory) / 'server-tick-probe.jar'
            probe.write_bytes(b'rebuilt probe')
            with patch('generate_candidate_manifest.controlled_path', return_value=probe):
                frozen = freeze_server_tick_probe(probe, sha256(probe))
                self.assertEqual(frozen, {'path': str(probe), 'sha256': sha256(probe)})
                probe.write_bytes(b'stale probe')
                with self.assertRaisesRegex(ValueError, 'differs from frozen source'):
                    freeze_server_tick_probe(probe, frozen['sha256'])

    def test_outside_private_namespace_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            probe = Path(directory) / 'probe.jar'
            probe.write_bytes(b'probe')
            with self.assertRaises(ValueError):
                freeze_server_tick_probe(probe, sha256(probe))


if __name__ == '__main__':
    unittest.main()
