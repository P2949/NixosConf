"""DH protocol and no-unwanted-generation qualification on a disposable clone."""

import argparse
import json
import math
import os
from pathlib import Path
import signal
import sys

from dh_database import inspect_closed_cache
from realtime_updates import qualify_realtime
from client_runtime import Client
from functional_clients import log_offset, wait_for_log_since
from functional_runtime import Lab
from qualification_manifest import canonical_bytes
from qualification_proof import write_proof
from world_semantics import region_occupancy, no_unwanted_generation
import maintenance


PLAYER = 'PerfProbe'
PLAYER_PRESENT_MARKER = 'QUALIFICATION_DH_PLAYER_PRESENT'
COMMAND_MARKER = 'QUALIFICATION_DH_COMMAND_OK'
DISCONNECT_MARKER = f'{PLAYER} left the game'


def qualification_exit_code(references):
    outcomes = {reference.get('result') for reference in references.values()}
    if 'FAIL' in outcomes:
        return 1
    if set(references) == {'dh_functional', 'no_unwanted_generation'} and outcomes == {'PASS'}:
        return 0
    return 2


def exercise_dh_client(lab, client):
    """Exercise ordinary play while the DH client/server session is active."""
    client.wait_joined()

    if not client.joined():
        raise RuntimeError(
            'DH client lost connection immediately after join'
        )

    offset = log_offset(lab.log)

    lab.send(
        f'execute if entity @a[name={PLAYER},limit=1] '
        f'run say {PLAYER_PRESENT_MARKER}'
    )

    wait_for_log_since(
        lab.log,
        PLAYER_PRESENT_MARKER,
        offset,
    )

    offset = log_offset(lab.log)

    lab.send(
        f'gamemode spectator @a[name={PLAYER},limit=1]'
    )
    lab.send(
        f'execute if entity '
        f'@a[name={PLAYER},gamemode=spectator,limit=1] '
        f'run say {COMMAND_MARKER}'
    )

    wait_for_log_since(
        lab.log,
        COMMAND_MARKER,
        offset,
    )

    if not client.joined():
        raise RuntimeError(
            'DH client disconnected after controlled server action'
        )

    disconnect_offset = log_offset(lab.log)

    client.wait_finished()

    wait_for_log_since(
        lab.log,
        DISCONNECT_MARKER,
        disconnect_offset,
    )


def read_dh_messages(path):
    """Parse the payload-free packet-type telemetry emitted by the DH probe."""
    if not path.exists():
        return []

    messages = []
    previous_time = None

    for line_number, line in enumerate(
        path.read_text().splitlines(),
        1,
    ):
        if not line:
            raise ValueError(
                f'empty DH telemetry line {line_number}'
            )

        try:
            message = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f'invalid DH telemetry JSON line {line_number}'
            ) from error

        if (
            not isinstance(message, dict)
            or set(message) != {
                'monotonic_ns',
                'type',
                'exception_type',
            }
        ):
            raise ValueError(
                f'invalid DH telemetry schema line {line_number}'
            )

        monotonic = message['monotonic_ns']
        message_type = message['type']
        exception_type = message['exception_type']

        if (
            type(monotonic) is not int
            or monotonic <= 0
            or not isinstance(message_type, str)
            or not message_type
            or not isinstance(exception_type, str)
        ):
            raise ValueError(
                f'invalid DH telemetry value line {line_number}'
            )

        if (
            previous_time is not None
            and monotonic < previous_time
        ):
            raise ValueError(
                'DH telemetry monotonic timestamps regressed'
            )

        previous_time = monotonic
        messages.append(message)

    return messages


def dh_outcome(messages, manifest=None):
    """Require data traffic; allow only the inspected binary's split response."""
    if not messages:
        return 'FAIL'

    verified_binary = manifest is not None and any(
        mod.get('id') == 'distanthorizons'
        and mod.get('sha256') == VERIFIED_DH_3_3_4_SHA256
        for mod in manifest.get('mods', [])
    )
    for message in messages:
        if message['type'] == 'ExceptionMessage' or message['exception_type']:
            if not (verified_binary and message['type'] == 'ExceptionMessage'
                    and message['exception_type'] == 'SectionRequiresSplittingException'):
                return 'FAIL'
    if not any(message['type'] in (
        'FullDataSourceResponseMessage', 'FullDataSplitMessage',
        'FullDataPartialUpdateMessage',
    ) and not message['exception_type'] for message in messages):
        return 'FAIL'

    return 'PASS'


# SHA-256 of the inspected 3.3.4 jar: split protocol response and read-side
# empty region shells are independently source-bound to this same artifact.
VERIFIED_DH_3_3_4_SHA256 = 'ba3e5c85a765a109219831df99b99ef5cfcdee05b2dfa6796116993bd48d3947'


def generation_outcome(before, after, manifest=None):
    # Entity and POI records change during ordinary play. Only terrain region
    # occupancy and generation status establish new terrain generation.
    terrain_before = {
        name: region for name, region in before.items()
        if Path(name).parent.name == 'region'
    }
    terrain_after = {
        name: region for name, region in after.items()
        if Path(name).parent.name == 'region'
    }
    # Pinned RegionFileStorageExternalCache.getRegionFile checks only the
    # parent directory before constructing RegionFile during reads. Permit
    # its empty shells only for the inspected binary, never arbitrary builds.
    verified_binary = manifest is not None and any(
        mod.get('id') == 'distanthorizons'
        and mod.get('sha256') == VERIFIED_DH_3_3_4_SHA256
        for mod in manifest.get('mods', [])
    )
    shells = [name for name, region in terrain_after.items()
              if name not in terrain_before and region['size'] == 0 and not region['chunks']]
    return (
        'PASS'
        if no_unwanted_generation(terrain_before, terrain_after,
                                 verified_empty_shells=shells if verified_binary else ())
        else 'FAIL'
    )


def chunk_count(regions):
    return sum(
        len(region['chunks'])
        for region in regions.values()
    )


def write_dh_proofs(
    manifest,
    output,
    lab,
    client_output,
    server_pid,
    client_pid,
    before,
    after,
):
    """Write both proofs only after client and server evidence is final."""
    if lab.active:
        raise RuntimeError(
            'DH proofs require stopped functional server'
        )

    result_path = client_output / 'result.json'
    heartbeat_path = client_output / 'heartbeat.json'
    launcher_log = client_output / 'launcher.log'
    messages_path = client_output / 'dh-received.jsonl'

    result = json.loads(result_path.read_text())
    heartbeat = json.loads(heartbeat_path.read_text())

    if result != {'result': 'PASS'}:
        raise RuntimeError(
            'DH client probe did not produce PASS'
        )

    elapsed = heartbeat.get('elapsed_seconds')

    if (
        not isinstance(heartbeat.get('connected'), bool)
        or not isinstance(elapsed, (int, float))
        or isinstance(elapsed, bool)
        or not math.isfinite(elapsed)
        or elapsed <= 0
    ):
        raise RuntimeError(
            'DH client heartbeat is malformed'
        )

    databases = inspect_closed_cache(
        Path(manifest['client']['root']) / 'instances/dh-clean/minecraft/Distant_Horizons_server_data',
        client_output, owner_stopped=not Path(f'/proc/{client_pid}').exists(),
    )
    database_receipt = client_output / 'dh-databases.json'
    database_receipt.write_bytes(canonical_bytes(databases))
    database_receipt.chmod(0o400)

    realtime_path = output / 'dh-realtime.json'
    realtime = json.loads(realtime_path.read_text())
    if realtime.get('result') != 'PASS' or realtime.get('restored') is not True:
        raise RuntimeError('DH real-time landmark proof did not pass')

    messages = read_dh_messages(messages_path)
    dh_result = dh_outcome(messages, manifest)
    terrain_result = generation_outcome(before, after, manifest)

    before_path = output / 'terrain-before.json'
    after_path = output / 'terrain-after.json'

    before_path.write_bytes(canonical_bytes(before))
    after_path.write_bytes(canonical_bytes(after))

    before_path.chmod(0o400)
    after_path.chmod(0o400)

    exceptions = [
        {
            'type': message['type'],
            'exception_type': message['exception_type'],
        }
        for message in messages
        if (
            message['type'] == 'ExceptionMessage'
            or message['exception_type']
        )
    ]

    dh_receipt = output / 'dh-functional.json'
    dh_receipt.write_text(
        json.dumps(
            {
                'result': dh_result,
                'profile': 'dh-clean',
                'player': PLAYER,
                'server_player_marker': PLAYER_PRESENT_MARKER,
                'server_command_marker': COMMAND_MARKER,
                'clean_disconnect_marker': DISCONNECT_MARKER,
                'client_probe_result': result,
                'final_heartbeat': heartbeat,
                'client_databases': databases,
                'real_time_updates': realtime,
                'dh_message_count': len(messages),
                'dh_message_types': sorted({
                    message['type']
                    for message in messages
                }),
                'dh_exceptions': exceptions,
                'server_pid': server_pid,
                'client_pid': client_pid,
                'server_world': str(lab.server),
                'baseline_uuid': (
                    manifest['baseline']['subvolume_uuid']
                ),
            },
            indent=2,
        )
        + '\n'
    )
    dh_receipt.chmod(0o400)

    terrain_receipt = output / 'no-unwanted-generation.json'
    terrain_receipt.write_text(
        json.dumps(
            {
                'result': terrain_result,
                'before_region_files': len(before),
                'after_region_files': len(after),
                'before_chunk_entries': chunk_count(before),
                'after_chunk_entries': chunk_count(after),
                'server_world': str(lab.server),
                'baseline_uuid': (
                    manifest['baseline']['subvolume_uuid']
                ),
            },
            indent=2,
        )
        + '\n'
    )
    terrain_receipt.chmod(0o400)

    dh_evidence = [
        (dh_receipt, 'json'),
        (result_path, 'json'),
        (heartbeat_path, 'json'),
        (launcher_log, 'log'),
        (lab.log, 'log'),
    ]

    dh_evidence.append((realtime_path, 'json'))
    dh_evidence.extend((Path(entry['path']), entry['type']) for entry in realtime['evidence'])
    dh_evidence.append((database_receipt, 'json'))
    dh_evidence.extend((Path(database['copy']), 'sqlite') for database in databases)

    if messages_path.exists():
        dh_evidence.insert(
            1,
            (messages_path, 'log'),
        )

    terrain_evidence = [
        (terrain_receipt, 'json'),
        (before_path, 'json'),
        (after_path, 'json'),
        (lab.log, 'log'),
    ]

    references = {
        'dh_functional': write_proof(
            manifest,
            'dh_functional',
            output / 'dh_functional-proof.json',
            dh_evidence,
            dh_result,
        ),
        'no_unwanted_generation': write_proof(
            manifest,
            'no_unwanted_generation',
            output / 'no_unwanted_generation-proof.json',
            terrain_evidence,
            terrain_result,
        ),
    }

    reference_path = output / 'dh-functional-reference.json'
    reference_path.write_bytes(
        canonical_bytes(references)
    )
    reference_path.chmod(0o400)

    return references


def execute(manifest, output):
    if 'client' not in manifest:
        raise ValueError(
            'functional client identity missing from candidate manifest'
        )

    lab = Lab(
        manifest,
        output,
    )

    (output / 'candidate-manifest.json').write_bytes(
        canonical_bytes(manifest)
    )

    try:
        maintenance.enter(output)

        with lab:
            before = region_occupancy(
                lab.server / 'world',
                include_status=True,
            )

            lab.start()

            client_output = output / 'client-dh'

            with Client(
                manifest,
                client_output,
                'dh-clean',
                45,
                fresh_cache=True,
            ) as client:
                exercise_dh_client(
                    lab,
                    client,
                )
                client_pid = client.pid

            qualify_realtime(lab, manifest, output, before)
            server_pid = lab.pid

        # Lab.__exit__ has finalized server-phase-1.log.
        after = region_occupancy(
            lab.server / 'world',
            include_status=True,
        )

        return write_dh_proofs(
            manifest,
            output,
            lab,
            client_output,
            server_pid,
            client_pid,
            before,
            after,
        )

    finally:
        try:
            lab.stop()
        finally:
            if (output / 'maintenance.json').exists():
                maintenance.restore(output)

                if (output / 'guard-armed').exists():
                    maintenance.disarm()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        '--manifest',
        type=Path,
        required=True,
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    if os.geteuid() != 0:
        parser.error('root required')

    os.umask(0o077)

    def terminate(signum, frame):
        raise SystemExit(
            'functional qualification interrupted'
        )

    signal.signal(
        signal.SIGTERM,
        terminate,
    )

    manifest = json.loads(
        args.manifest.read_text()
    )

    references = execute(manifest, args.output)
    print(json.dumps(references))
    sys.exit(qualification_exit_code(references))
