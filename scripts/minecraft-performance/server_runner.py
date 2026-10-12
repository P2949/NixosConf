"""Private loopback console bridge for a disposable Nix-built benchmark server."""

import argparse
import os
import signal
import socket
import subprocess
from pathlib import Path

GRACEFUL_STOP_SECONDS = 300
FORCED_STOP_SECONDS = 15


MAX_COMMAND_BYTES = 8191


def read_frame(connection, maximum):
    """Read one bounded newline frame; the sender must half-close its stream."""
    data = bytearray()
    while True:
        part = connection.recv(min(4096, maximum + 2 - len(data)))
        if not part:
            if not data.endswith(b'\n'):
                raise ValueError('incomplete console frame')
            payload = bytes(data[:-1])
            if not payload or b'\n' in payload or b'\r' in payload:
                raise ValueError('invalid console frame')
            payload.decode('utf-8', errors='strict')
            return payload
        data.extend(part)
        if len(data) > maximum + 1:
            raise ValueError('console frame exceeds bound')


def force_stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=FORCED_STOP_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=FORCED_STOP_SECONDS)


def cleanup(process, listener, console, receipt):
    try:
        force_stop(process)
    finally:
        try:
            listener.close()
        finally:
            try:
                console.unlink(missing_ok=True)
            finally:
                if receipt is not None:
                    from server_exit import write_receipt
                    write_receipt(receipt, process)


def graceful_stop(process):
    process.stdin.write("stop\n")
    process.stdin.flush()
    process.wait(timeout=GRACEFUL_STOP_SECONDS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--console", type=Path, required=True)
    parser.add_argument('--exit-receipt', type=Path)
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
    if args.exit_receipt is not None and (args.exit_receipt.parent != args.console.parent
            or args.exit_receipt != args.exit_receipt.resolve() or args.exit_receipt.exists()):
        parser.error('exit receipt must be new canonical console sibling')
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
                connection.settimeout(10)
                try:
                    data = read_frame(connection, MAX_COMMAND_BYTES)
                except (ValueError, UnicodeError, TimeoutError):
                    connection.sendall(b"INVALID\n")
                    continue
                process.stdin.write(data.decode("utf-8") + "\n")
                process.stdin.flush()
                connection.sendall(b"QUEUED\n")
                connection.shutdown(socket.SHUT_WR)
        if process.poll() is None:
            graceful_stop(process)
    finally:
        cleanup(process, listener, args.console, args.exit_receipt)
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
