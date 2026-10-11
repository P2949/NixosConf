from pathlib import Path
import struct
import zlib
import tempfile
import unittest

from world_semantics import no_unwanted_generation, region_occupancy


class TerrainAcceptanceTests(unittest.TestCase):
    def test_verified_empty_shell_is_not_a_generated_chunk(self):
        before = {'region/r.0.0.mca': {'size': 12288, 'chunks': [(0, 0)]}}
        after = {**before, 'region/r.1.0.mca': {'size': 0, 'chunks': []}}
        self.assertFalse(no_unwanted_generation(before, after))
        self.assertTrue(no_unwanted_generation(before, after, ['region/r.1.0.mca']))
        after['region/r.1.0.mca'] = {'size': 8192, 'chunks': []}
        self.assertFalse(no_unwanted_generation(before, after, ['region/r.1.0.mca']))
        after = {'region/r.0.0.mca': {'size': 16384, 'chunks': [(0, 0), (1, 0)]}}
        self.assertFalse(no_unwanted_generation(before, after))

    def test_region_header_coordinates_and_invalid_payloads(self):
        with tempfile.TemporaryDirectory() as directory:
            world = Path(directory)
            region = world / 'region'
            region.mkdir()
            path = region / 'r.-1.2.mca'
            data = bytearray(12288)
            struct.pack_into('>I', data, 33 * 4, (2 << 8) | 1)
            struct.pack_into('>I', data, 8192, 2)
            data[8196:8198] = b'\x02x'
            path.write_bytes(data)
            self.assertEqual(region_occupancy(world)['region/r.-1.2.mca']['chunks'], [(-31, 65)])
            path.write_bytes(data[:8198])
            self.assertEqual(region_occupancy(world)['region/r.-1.2.mca']['chunks'], [(-31, 65)])
            path.write_bytes(data[:8197])
            with self.assertRaises(ValueError):
                region_occupancy(world)
            struct.pack_into('>I', data, 8192, 8192)
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                region_occupancy(world)

    def test_full_chunk_status_and_header_coordinates_are_independent_checks(self):
        def text(value):
            data = value.encode()
            return struct.pack('>H', len(data)) + data
        payload = (b'\x0a\x00\x00' + b'\x08' + text('Status') + text('minecraft:full')
                   + b'\x03' + text('xPos') + struct.pack('>i', 512)
                   + b'\x03' + text('zPos') + struct.pack('>i', 512) + b'\x00')
        compressed = zlib.compress(payload)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'region').mkdir()
            data = bytearray(12288)
            struct.pack_into('>I', data, 0, (2 << 8) | 1)
            struct.pack_into('>I', data, 8192, len(compressed) + 1)
            data[8196] = 2
            data[8197:8197 + len(compressed)] = compressed
            path = root / 'region/r.16.16.mca'
            path.write_bytes(data)
            before = region_occupancy(root, include_status=True)
            self.assertEqual(before['region/r.16.16.mca']['chunk_metadata'][0]['Status'], 'minecraft:full')
            path.rename(root / 'region/r.15.16.mca')
            with self.assertRaisesRegex(ValueError, 'coordinate'):
                region_occupancy(root, include_status=True)
            after = {'region/r.16.16.mca': {**before['region/r.16.16.mca'],
                     'chunk_metadata': [{'xPos': 512, 'zPos': 512, 'Status': 'minecraft:terrain'}]}}
            self.assertFalse(no_unwanted_generation(before, after))


if __name__ == '__main__':
    unittest.main()
