from pathlib import Path
import struct
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


if __name__ == '__main__':
    unittest.main()
