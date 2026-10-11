from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dh_idle_attribution import collect_sample, disk_state
from idle_metrics import cpu_percent, host_cpu, io_delta, rapl_delta, unique_java, validate_rapl


class CounterTests(unittest.TestCase):
    def test_wraparound_and_reset_are_distinct(self):
        self.assertEqual(rapl_delta(950, 50, 1000, 1), 100)
        for before, after, maximum, duration in [(500, 100, 1000, 1), (0, 1000, 1000, 1),
                                                  (0, 1, 0, 1), (0, 1, 1000, 0),
                                                  (0, 300000000, 1000000000, 1)]:
            with self.assertRaises(ValueError):
                rapl_delta(before, after, maximum, duration)

    def test_interval_cpu_and_host_accounting(self):
        self.assertEqual(cpu_percent(0, 100000, 10), 1)
        self.assertEqual(host_cpu('cpu 0 0 0 0 0 0 0 0 900',
                                 'cpu 30 0 20 50 0 0 0 0 999'), 50)
        with self.assertRaises(ValueError):
            cpu_percent(10, 9, 1)
        with self.assertRaises(ValueError):
            host_cpu('cpu 1 0 0 0 0 0 0 0', 'cpu 0 0 0 1 0 0 0 0')

    def test_io_new_devices_and_counter_disappearance(self):
        result = io_delta('8:0 rbytes=10 wbytes=20',
                          '8:0 rbytes=15 wbytes=30\n8:1 rbytes=5 wbytes=7')
        self.assertEqual((result['rbytes'], result['wbytes']), (10, 17))
        for after in ('', '8:0 rbytes=0 wbytes=0'):
            with self.assertRaises(ValueError):
                io_delta('8:0 rbytes=10 wbytes=20', after)

    def test_identity_preflight_and_java_uniqueness(self):
        validate_rapl('package-0', 1, 1000)
        for args in [('core', 1, 1000), ('package-0', 0, 1000), ('package-0', 1, 0)]:
            with self.assertRaises(ValueError):
                validate_rapl(*args)
        self.assertEqual(unique_java([123]), 123)
        for pids in ([], [123, 456]):
            with self.assertRaises(ValueError):
                unique_java(pids)

    def test_same_size_database_mutation_changes_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p = root / 'DistantHorizons.sqlite'
            p.write_bytes(b'a' * 4096)
            before = disk_state(root)
            p.write_bytes(b'b' * 4096)
            self.assertNotEqual(before, disk_state(root))

    def test_clean_sampling_never_invokes_diagnostic_collectors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename, value in {'cpu.stat': 'usage_usec 100\n', 'memory.events': 'high 0\n',
                                    'memory.current': '1000', 'io.stat': '', 'energy_uj': '10',
                                    'host': 'cpu 1 0 0 1 0 0 0 0\n'}.items():
                (root / filename).write_text(value)
            with patch('dh_idle_attribution.threads', return_value={}) as threads, \
                    patch('dh_idle_attribution.idle_residency', return_value={}) as residency:
                clean = collect_sample(root, root, 'clean', 123, root / 'host')
                self.assertNotIn('threads', clean)
                threads.assert_not_called()
                residency.assert_not_called()
                diagnostic = collect_sample(root, root, 'diagnostic', 123, root / 'host')
                self.assertIn('threads', diagnostic)
                threads.assert_called_once_with(123)
                residency.assert_called_once()
            (root / 'cpu.stat').unlink()
            with self.assertRaises(FileNotFoundError):
                collect_sample(root, root, 'clean', 123, root / 'host')


if __name__ == '__main__':
    unittest.main()


class ToolPathRegressionTests(unittest.TestCase):
    def test_idle_tools_come_from_frozen_nix_input(self):
        root = Path(__file__).resolve().parent
        source = (root / 'dh_idle_attribution.py').read_text()
        self.assertNotRegex(source, r'/nix/store/[a-z0-9]{32}-coreutils')
        self.assertIn("CANDIDATE['qualification_tools_path']", source)
        self.assertIn('qualification_tools_path = pkgs.lib.makeBinPath',
                      (root / 'candidate.nix').read_text())
