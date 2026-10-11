"""Region occupancy acceptance distinct from strict paused-idle content equality."""

import re
import struct
from pathlib import Path
import zlib


def nbt_chunk_metadata(data):
    """Bounded NBT scan; retain only status/coordinates, never block palettes."""
    view = memoryview(data)
    cursor = 0
    def read(size):
        nonlocal cursor
        if size < 0 or cursor + size > len(view):
            raise ValueError('truncated chunk NBT')
        result = view[cursor:cursor + size]
        cursor += size
        return result
    def number(fmt):
        return struct.unpack('>' + fmt, read(struct.calcsize(fmt)))[0]
    def string(decode=True):
        value = read(number('H'))
        return bytes(value).decode() if decode else None
    def tag_value(tag, keep=False, depth=0):
        if depth > 64:
            raise ValueError('chunk NBT nesting bound')
        if tag in (1, 2, 3, 4, 5, 6):
            value = number({1: 'b', 2: 'h', 3: 'i', 4: 'q', 5: 'f', 6: 'd'}[tag])
            return value if keep else None
        if tag == 8:
            value = string(keep)
            return value if keep else None
        if tag in (7, 11, 12):
            size = number('i')
            if not 0 <= size <= 10000000:
                raise ValueError('chunk NBT array bound')
            read(size * {7: 1, 11: 4, 12: 8}[tag])
            return None
        if tag == 9:
            member, size = number('B'), number('i')
            if not 0 <= size <= 1000000:
                raise ValueError('chunk NBT list bound')
            for _ in range(size):
                tag_value(member, False, depth + 1)
            return None
        if tag == 10:
            result = {}
            while (member := number('B')) != 0:
                key = string(keep)
                selected = keep and key in ('Status', 'xPos', 'zPos', 'Level')
                value = tag_value(member, selected, depth + 1)
                if selected:
                    if key in result:
                        raise ValueError('duplicate chunk metadata key')
                    result[key] = value
            return result
        raise ValueError('unknown chunk NBT tag')
    if number('B') != 10:
        raise ValueError('chunk NBT root must be compound')
    string(False)
    metadata = tag_value(10, True)
    if 'Level' in metadata:
        metadata = metadata['Level']
    if (not isinstance(metadata.get('Status'), str)
            or not all(type(metadata.get(key)) is int for key in ('xPos', 'zPos'))):
        raise ValueError('missing chunk status/coordinates')
    return metadata


def chunk_payload_metadata(stream, sector):
    stream.seek(sector * 4096)
    length = struct.unpack('>I', stream.read(4))[0]
    compression = stream.read(1)[0]
    payload = stream.read(length - 1)
    if compression in (1, 2):
        decoder = zlib.decompressobj(31 if compression == 1 else 15)
        payload = decoder.decompress(payload, 32 * 1024 * 1024 + 1)
        if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError('invalid or oversized compressed chunk')
    elif compression != 3:
        raise ValueError('unsupported chunk compression/external storage')
    if len(payload) > 32 * 1024 * 1024:
        raise ValueError('chunk payload exceeds metadata inspection bound')
    return nbt_chunk_metadata(payload)


def region_occupancy(world, *, include_status=False):
    regions = {}
    for path in sorted(Path(world).rglob('*.mca')):
        match = re.fullmatch(r'r\.(-?\d+)\.(-?\d+)\.mca', path.name)
        if match is None or path.parent.name not in ('region', 'entities', 'poi') or path.is_symlink():
            raise ValueError('unexpected region path')
        size = path.stat().st_size
        coordinates = []
        metadata = []
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
                    if include_status and path.parent.name == 'region':
                        chunk = chunk_payload_metadata(stream, sector)
                        if (chunk['xPos'], chunk['zPos']) != coordinates[-1]:
                            raise ValueError('NBT coordinate disagrees with region slot')
                        metadata.append(chunk)
        regions[str(path.relative_to(world))] = {'size': size, 'chunks': coordinates}
        if include_status and path.parent.name == 'region':
            regions[str(path.relative_to(world))]['chunk_metadata'] = metadata
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
        elif 'chunk_metadata' in previous and region.get('chunk_metadata') != previous['chunk_metadata']:
            return False
    return True
