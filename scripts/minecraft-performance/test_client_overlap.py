from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from client_overlap import minecraft_clients
from dh_idle_attribution import collect_sample


class OverlapTests(unittest.TestCase):
    def test_known_client_excluded_by_group_and_unrelated_java_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for pid, main, group in ((123, 'net.minecraft.client.main.Main', '/other'),
                                     (124, 'net.fabricmc.loader.impl.launch.knot.KnotClient', '/qualification'),
                                     (125, 'org.example.Build', '/build')):
                process = root / str(pid)
                process.mkdir()
                (process / 'comm').write_text('java\n')
                (process / 'cmdline').write_bytes((main + '\0--accessToken\0secret\0').encode())
                (process / 'cgroup').write_text('0::' + group + '\n')
                (process / 'cwd').symlink_to(root)
            found = minecraft_clients(proc=root, excluded_group='/qualification')
            self.assertEqual(found, [{'pid': 123, 'reason': 'client_main_class'}])
            self.assertNotIn('secret', str(found))
            (root / '123' / 'comm').write_text('build\n')
            self.assertEqual(minecraft_clients(proc=root, excluded_group='/qualification'), [])

    def test_transient_mid_window_client_is_retained_in_samples(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, text in {'cpu.stat': 'usage_usec 1', 'memory.events': 'oom 0',
                               'memory.current': '1', 'io.stat': '', 'energy_uj': '1',
                               'stat': 'cpu 1 1 1 1 1 1 1 1'}.items():
                (root / name).write_text(text)
            conflict = [{'pid': 42, 'reason': 'client_main_class'}]
            with patch('dh_idle_attribution.minecraft_clients', side_effect=[[], conflict, []]):
                rows = [collect_sample(root, root, 'clean', 1, root / 'stat') for _ in range(3)]
            self.assertTrue(any(row['outside_clients'] for row in rows))
            self.assertEqual(rows[0]['outside_clients'], rows[-1]['outside_clients'])
