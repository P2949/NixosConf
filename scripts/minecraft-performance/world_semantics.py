"""Region occupancy acceptance distinct from strict paused-idle content equality."""

import re
import struct
from pathlib import Path


def region_occupancy(world):
    regions = {}
    for path in sorted(Path(world).rglob('*.mca')):
        match = re.fullmatch(r'r\.(-?\d+)\.(-?\d+)\.mca', path.name)
        if match is None or path.parent.name not in ('region', 'entities', 'poi') or path.is_symlink():
            raise ValueError('unexpected region path')
        size = path.stat().st_size
        coordinates = []
        if size:
            # A valid final sector can end immediately after its payload.
            if size < 8192:
                raise ValueError('malformed region size')
            with path.open('rb') as stream:
                locations = struct.unpack('>1024I', stream.read(4096))
                occupied = set()
                for index, location in enumerate(locations):
                    if location == 0:
                        continue
                    sector, count = location >> 8, location & 255
                    if (sector < 2 or count == 0 or (sector + count) > (size + 4095) // 4096
                            or sector * 4096 + 4 > size):
                        raise ValueError('invalid region chunk location')
                    allocation = set(range(sector, sector + count))
                    if allocation & occupied:
                        raise ValueError('overlapping region chunk allocation')
                    occupied.update(allocation)
                    stream.seek(sector * 4096)
                    length = struct.unpack('>I', stream.read(4))[0]
                    if length < 1 or length + 4 > count * 4096 or sector * 4096 + length + 4 > size:
                        raise ValueError('invalid region chunk payload length')
                    coordinates.append((int(match.group(1)) * 32 + index % 32,
                                        int(match.group(2)) * 32 + index // 32))
        regions[str(path.relative_to(world))] = {'size': size, 'chunks': coordinates}
    return regions


def no_unwanted_generation(before, after, verified_empty_shells=()):
    """Only explicitly source-verified zero-byte shells may be newly present."""
    shells = set(verified_empty_shells)
    if set(before) - set(after):
        return False
    for filename, region in after.items():
        previous = before.get(filename)
        if previous is None:
            if filename not in shells or region['size'] != 0 or region['chunks']:
                return False
        elif set(map(tuple, region['chunks'])) != set(map(tuple, previous['chunks'])):
            return False
    return True
