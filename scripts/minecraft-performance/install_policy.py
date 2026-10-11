"""Install a writable Nix policy template in a disposable server clone."""

import argparse
import os
import stat
from pathlib import Path


def install(source, destination):
    destination = Path(destination)
    parent = destination.parent.resolve()
    if parent.is_relative_to(Path('/srv/minecraft')):
        raise ValueError('production directory prohibited')
    owner = parent.stat()
    if destination.is_symlink():
        raise ValueError('configuration destination must not be a symlink')
    destination.write_bytes(Path(source).read_bytes())
    os.chown(destination, owner.st_uid, owner.st_gid)
    destination.chmod(0o660)
    actual = destination.stat()
    if (actual.st_uid, actual.st_gid, stat.S_IMODE(actual.st_mode)) != (owner.st_uid, owner.st_gid, 0o660):
        raise ValueError('configuration ownership or permissions were not applied')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    install(args.source, args.destination)
