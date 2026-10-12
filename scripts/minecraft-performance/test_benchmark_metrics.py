import csv
from pathlib import Path
import tempfile
import unittest

from benchmark_metrics import CLIENT_FRAME_COLUMN, client_metrics, jfr_gc_metrics, read_window, resource_metrics


class BenchmarkWindowTests(unittest.TestCase):
    def test_client_reader_accepts_the_java_probe_header_and_window(self):
        source = (Path(__file__).parent / 'probe/FrameBuffer.java').read_text()
        import re
        header = re.search(r'"(monotonic_ns,[^"\\]+)\\n"', source)[1]
        self.assertIn(CLIENT_FRAME_COLUMN, header.split(','))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'frames.csv'
            with path.open('w') as stream:
                stream.write(header + '\n')
                writer = csv.writer(stream)
                for i in range(1, 401):
                    writer.writerow([i * 100000000, 10])
            result = client_metrics(path, 10, 30)
            self.assertEqual(result['client_1pct_fps'], 100)

    def test_probe_excludes_warmup_and_rejects_truncated_window(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'ticks.csv'
            with p.open('w') as stream:
                writer = csv.writer(stream)
                writer.writerow(['monotonic_ns', 'tick_ms'])
                for i in range(1, 401):
                    writer.writerow([i * 100000000, 999 if i < 100 else 1])
            self.assertEqual(set(read_window(p, 10, 30, 'tick_ms')), {1})
            with self.assertRaises(ValueError):
                read_window(p, 10, 80, 'tick_ms')

    def test_owned_cpu_removed_from_environment_gate(self):
        rows = []
        for i in range(21):
            rows.append(dict(time=i + 1, service_us=i * 1000000,
                client_us=i * 1000000, host_cpu=f'cpu {i * 20} 0 0 {i * 80} 0 0 0 0',
                memory_bytes=100, memory_events=dict(high=0, max=0, oom=0, oom_kill=0),
                io=f'1:1 rbytes={i} wbytes={i * 2} rios=0 wios=0 dbytes=0 dios=0'))
        result = resource_metrics(rows, 1, 21, 10, 200)
        self.assertTrue(result['environment_valid'])
        self.assertEqual(result['cpu_pct'], 100)
        self.assertEqual(result['io']['wbytes'], 40)
        rows[-1]['memory_events']['oom'] = -1
        with self.assertRaises(ValueError):
            resource_metrics(rows, 1, 21, 10, 200)

    def test_candidate_memory_threshold_changes_pressure_classification(self):
        rows = [dict(time=i + 1, service_us=i, client_us=0,
                     host_cpu=f'cpu {i} 0 0 {i * 99} 0 0 0 0',
                     memory_bytes=9 * 1024 ** 3,
                     memory_events=dict(high=i, max=0, oom=0, oom_kill=0), io='')
                for i in range(21)]
        self.assertTrue(resource_metrics(rows, 1, 21, 12, 8 * 1024 ** 3)['severe_memory_high'])
        self.assertFalse(resource_metrics(rows, 1, 21, 12, 11 * 1024 ** 3)['severe_memory_high'])
        for value in (True, float('nan'), float('inf'), 0):
            with self.assertRaises(ValueError):
                resource_metrics(rows, 1, 21, 12, value)

    def test_jfr_filters_window_and_reads_pause_units(self):
        recording = {'recording': {'events': [
            {'type': 'jdk.GarbageCollection', 'values': {'startTime': '2026-10-12T00:00:00Z'}},
            {'type': 'jdk.GCPhasePause', 'values': {'startTime': '2026-10-12T00:00:00Z', 'duration': 'PT0.002S'}},
            {'type': 'jdk.GCPhasePause', 'values': {'startTime': '2026-10-11T00:00:00Z', 'duration': 'PT1S'}}]}}
        from datetime import datetime
        stamp = datetime.fromisoformat('2026-10-12T00:00:00+00:00').timestamp()
        result = jfr_gc_metrics(recording, stamp - 1, stamp + 1)
        self.assertEqual(result['gc_collections'], 1)
        self.assertEqual(result['gc_pause_total_ms'], 2)


if __name__ == '__main__':
    unittest.main()
