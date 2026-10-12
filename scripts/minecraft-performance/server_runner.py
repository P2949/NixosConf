"""Private loopback console bridge for a disposable Nix-built benchmark server."""

import argparse
import os
import signal
import socket
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--console", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if len(str(args.console).encode()) >= 108:
        parser.error('console exceeds Linux UNIX socket path limit')
    if not args.command:
        parser.error("server command required")
    if Path.cwd().resolve().is_relative_to(Path("/srv/minecraft")):
        parser.error("production data directory prohibited")
    if (not args.console.is_absolute() or '..' in args.console.parts
            or args.console != args.console.resolve() or args.console.exists()
            or not args.console.is_relative_to('/persist')
            or not args.console.parent.name.startswith('minecraft-performance')
                and not args.console.parent.parent.name.startswith('minecraft-performance')):
        parser.error("console must be new and canonical inside private qualification data")
    listener = socket.socket(socket.AF_UNIX)
    listener.bind(str(args.console))
    os.chmod(args.console, 0o600)
    listener.listen(1)
    listener.settimeout(1)
    process = subprocess.Popen(args.command, stdin=subprocess.PIPE, text=True)
    stopping = False

    def stop(_sig, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while process.poll() is None and not stopping:
            try:
                connection, _ = listener.accept()
            except TimeoutError:
                continue
            with connection:
                # One bounded UTF-8 command per connection, no shell execution.
                data = connection.recv(8192)
                if not data or len(data) == 8192 or b"\n" in data or b"\r" in data:
                    connection.sendall(b"INVALID\n")
                    continue
                process.stdin.write(data.decode("utf-8") + "\n")
                process.stdin.flush()
                connection.sendall(b"QUEUED\n")
        if process.poll() is None:
            process.stdin.write("stop\n")
            process.stdin.flush()
            process.wait(timeout=100)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=15)
        listener.close()
        args.console.unlink(missing_ok=True)
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
