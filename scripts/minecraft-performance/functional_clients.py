"""Bounded client compatibility qualification against a disposable candidate."""

import argparse
import json
import os
from pathlib import Path
import signal
import time

from client_runtime import Client
from functional_runtime import Lab
from qualification_manifest import canonical_bytes
from qualification_proof import write_proof
import maintenance


PLAYER = 'PerfProbe'
PLAYER_PRESENT_MARKER = 'QUALIFICATION_NON_DH_PLAYER_PRESENT'
COMMAND_MARKER = 'QUALIFICATION_NON_DH_COMMAND_OK'
DISCONNECT_MARKER = f'{PLAYER} left the game'


def log_offset(path):
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def wait_for_log_since(path, marker, offset, timeout=30):
    """Require a marker written after a known byte offset, never an old match."""
    deadline = time.monotonic() + timeout
    needle = marker.encode()

    while True:
        try:
            size = path.stat().st_size
            if size < offset:
                raise RuntimeError('functional server log unexpectedly shrank')

            with path.open('rb') as stream:
                stream.seek(offset)
                if needle in stream.read():
                    return
        except FileNotFoundError:
            pass

        if time.monotonic() >= deadline:
            raise RuntimeError('bounded functional log condition failed: ' + marker)

        time.sleep(0.25)


def exercise_non_dh_client(lab, client):
    """Prove a non-DH client remains compatible with the DH-enabled server."""
    client.wait_joined()

    if not client.joined():
        raise RuntimeError('non-DH client lost connection immediately after join')

    # Do not accept the ordinary join message as proof that our command ran.
    # Emit a unique marker only if the server currently resolves PerfProbe as
    # a live player entity.
    offset = log_offset(lab.log)
    lab.send(
        f'execute if entity @a[name={PLAYER},limit=1] '
        f'run say {PLAYER_PRESENT_MARKER}'
    )
    wait_for_log_since(lab.log, PLAYER_PRESENT_MARKER, offset)

    # Exercise a real server->player command without generating new terrain.
    # A second marker is emitted only if the server subsequently observes the
    # target player in spectator mode.
    offset = log_offset(lab.log)
    lab.send(f'gamemode spectator @a[name={PLAYER},limit=1]')
    lab.send(
        f'execute if entity @a[name={PLAYER},gamemode=spectator,limit=1] '
        f'run say {COMMAND_MARKER}'
    )
    wait_for_log_since(lab.log, COMMAND_MARKER, offset)

    if not client.joined():
        raise RuntimeError('non-DH client disconnected after controlled server action')

    # The client probe remains connected for its complete bounded duration,
    # writes PASS, disconnects, and terminates its JVM.
    disconnect_offset = log_offset(lab.log)
    client.wait_finished()
    wait_for_log_since(lab.log, DISCONNECT_MARKER, disconnect_offset)


def execute(manifest, output):
    if 'client' not in manifest:
        raise ValueError('functional client identity missing from candidate manifest')

    lab = Lab(manifest, output)
    (output / 'candidate-manifest.json').write_bytes(canonical_bytes(manifest))

    try:
        maintenance.enter(output)

        with lab:
            lab.start()

            client_output = output / 'client-no-dh'

            with Client(
                manifest,
                client_output,
                'no-dh',
                45,
            ) as client:
                exercise_non_dh_client(lab, client)

            result_path = client_output / 'result.json'
            heartbeat_path = client_output / 'heartbeat.json'
            launcher_log = client_output / 'launcher.log'

            result = json.loads(result_path.read_text())
            heartbeat = json.loads(heartbeat_path.read_text())

            if result.get('result') != 'PASS':
                raise RuntimeError('non-DH client probe did not produce PASS')

            receipt = output / 'non-dh-client.json'
            receipt.write_text(json.dumps({
                'result': 'PASS',
                'profile': 'no-dh',
                'player': PLAYER,
                'server_player_marker': PLAYER_PRESENT_MARKER,
                'server_command_marker': COMMAND_MARKER,
                'clean_disconnect_marker': DISCONNECT_MARKER,
                'client_probe_result': result,
                'final_heartbeat': heartbeat,
                'server_pid': lab.pid,
                'client_pid': client.pid,
                'production_data_touched': False,
            }, indent=2) + '\n')

            evidence = [
                (receipt, 'json'),
                (result_path, 'json'),
                (heartbeat_path, 'json'),
                (launcher_log, 'log'),
                (lab.log, 'log'),
            ]

            reference = write_proof(
                manifest,
                'non_dh_client',
                output / 'non_dh_client-proof.json',
                evidence,
                'PASS',
            )

            references = {'non_dh_client': reference}
            (output / 'functional-acceptance.json').write_text(
                json.dumps(references, indent=2) + '\n'
            )

            return references

    finally:
        try:
            lab.stop()
        finally:
            if (output / 'maintenance.json').exists():
                maintenance.restore(output)

                if (output / 'guard-armed').exists():
                    maintenance.disarm()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    if os.geteuid() != 0:
        parser.error('root required')

    os.umask(0o077)

    def terminate(signum, frame):
        raise SystemExit('functional qualification interrupted')

    signal.signal(signal.SIGTERM, terminate)

    manifest = json.loads(args.manifest.read_text())
    print(json.dumps(execute(manifest, args.output)))
