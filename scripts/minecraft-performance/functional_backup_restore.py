"""Real-backup and isolated playable-restore qualification."""

import argparse
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
from uuid import UUID

from dh_database import inspect_closed_database, inspect_closed_cache
from functional_dh import exercise_dh_client, read_dh_messages, dh_outcome
from client_runtime import Client
from functional_clients import exercise_non_dh_client
from functional_runtime import Lab
from qualification_manifest import (
    canonical_bytes,
    controlled_path,
    validate_candidate,
)
from qualification_proof import write_proof
import maintenance


HERE = Path(__file__).resolve().parent
SNAPSHOT_ROOT = Path('/.snapshots/minecraft')


def command(*args):
    return subprocess.check_output(
        args,
        text=True,
    ).strip()


def checked_uuid(value):
    return str(
        UUID(value)
    )


def require_healthy_status(status):
    if (
        not isinstance(status, dict)
        or status.get('health') != 'ok'
        or status.get('live_verification') != 'passed'
    ):
        raise RuntimeError(
            'verified live backup health required'
        )

    point = (
        status.get('state', {})
        .get('last_success', {})
    )

    required = (
        'snapshot_uuid',
        'filesystem_uuid',
        'snapshot_path',
        'created_at',
    )

    if not all(
        isinstance(point.get(key), str)
        and point[key]
        for key in required
    ):
        raise RuntimeError(
            'verified last-success recovery point required'
        )

    checked_uuid(
        point['snapshot_uuid']
    )
    checked_uuid(
        point['filesystem_uuid']
    )

    return point


def require_fresh_backup(before, after):
    previous = require_healthy_status(before)
    current = require_healthy_status(after)

    attempt = (
        after.get('state', {})
        .get('last_attempt', {})
    )

    if attempt.get('result') != 'success':
        raise RuntimeError(
            'qualification backup attempt did not succeed'
        )

    if (
        current['snapshot_uuid']
        == previous['snapshot_uuid']
        or current['snapshot_path']
        == previous['snapshot_path']
    ):
        raise RuntimeError(
            'maintenance did not produce a fresh recovery point'
        )

    return current


def metadata_value(text, name):
    match = re.search(
        rf'^\s*{re.escape(name)}:\s*(\S+)\s*$',
        text,
        re.MULTILINE,
    )

    if match is None:
        raise RuntimeError(
            f'Btrfs metadata missing {name}'
        )

    return match.group(1)


def parse_subvolume_identity(
    path,
    metadata,
    readonly,
    filesystem_uuid,
):
    uuid = checked_uuid(
        metadata_value(
            metadata,
            'UUID',
        )
    )

    parent = metadata_value(
        metadata,
        'Parent UUID',
    )

    parent_uuid = (
        None
        if parent == '-'
        else checked_uuid(parent)
    )

    if readonly not in (
        'ro=true',
        'ro=false',
    ):
        raise RuntimeError(
            'invalid Btrfs readonly property'
        )

    return {
        'path': str(path),
        'subvolume_uuid': uuid,
        'parent_uuid': parent_uuid,
        'filesystem_uuid': checked_uuid(
            filesystem_uuid
        ),
        'readonly': readonly == 'ro=true',
    }


def subvolume_identity(path):
    path = Path(path)

    if (
        not path.is_absolute()
        or path.is_symlink()
        or not path.is_dir()
        or path.resolve() != path
    ):
        raise RuntimeError(
            'unsafe Btrfs subvolume path'
        )

    metadata = command(
        'btrfs',
        'subvolume',
        'show',
        str(path),
    )

    readonly = command(
        'btrfs',
        'property',
        'get',
        '-t',
        's',
        str(path),
        'ro',
    )

    filesystem_uuid = command(
        'findmnt',
        '--noheadings',
        '--output',
        'UUID',
        '--target',
        str(path),
    )

    return parse_subvolume_identity(
        path,
        metadata,
        readonly,
        filesystem_uuid,
    )


def verify_recovery_point(point):
    path = Path(
        point['snapshot_path']
    )

    if (
        path.parent != SNAPSHOT_ROOT
        or not path.name.startswith('survival-')
    ):
        raise RuntimeError(
            'backup recovery point is outside managed snapshot namespace'
        )

    identity = subvolume_identity(
        path
    )

    if (
        identity['subvolume_uuid']
        != checked_uuid(point['snapshot_uuid'])
        or identity['filesystem_uuid']
        != checked_uuid(point['filesystem_uuid'])
        or not identity['readonly']
    ):
        raise RuntimeError(
            'backup recovery point identity differs from live receipt'
        )

    return identity


def prepare_output(output):
    output = controlled_path(
        output,
        Path('/persist'),
    )

    if (
        output.parent != Path('/persist')
        or not output.name.startswith(
            'minecraft-performance-functional-'
        )
    ):
        raise ValueError(
            'functional output must be a direct private namespace'
        )

    output.mkdir(
        mode=0o700,
    )
    output.chmod(
        0o700
    )

    subprocess.run(
        [
            'chown',
            'root:root',
            str(output),
        ],
        check=True,
    )

    return output


def replace_lab_root_with_snapshot(
    lab,
    snapshot_identity,
):
    if lab.active:
        raise RuntimeError(
            'restore clone replacement requires stopped lab'
        )

    source = Path(
        snapshot_identity['path']
    )

    if (
        lab.root.parent != lab.output
        or not lab.root.exists()
        or lab.root != lab.root.resolve()
    ):
        raise RuntimeError(
            'functional baseline clone is not owned'
        )

    existing = subvolume_identity(lab.root)
    baseline = lab.manifest['baseline']
    if (
        existing['readonly']
        or existing['parent_uuid'] != baseline['subvolume_uuid']
        or existing['filesystem_uuid'] != baseline['filesystem_uuid']
    ):
        raise RuntimeError('functional baseline clone identity mismatch before deletion')

    subprocess.run(
        [
            'btrfs',
            'subvolume',
            'delete',
            str(lab.root),
        ],
        check=True,
    )

    if lab.root.exists():
        raise RuntimeError(
            'functional baseline clone deletion did not complete'
        )

    subprocess.run(
        [
            'btrfs',
            'subvolume',
            'snapshot',
            str(source),
            str(lab.root),
        ],
        check=True,
    )

    clone = subvolume_identity(
        lab.root
    )

    if (
        clone['readonly']
        or clone['parent_uuid']
        != snapshot_identity['subvolume_uuid']
        or clone['filesystem_uuid']
        != snapshot_identity['filesystem_uuid']
    ):
        raise RuntimeError(
            'writable restore clone identity mismatch'
        )

    actual_server = controlled_path(
        lab.root / 'survival',
        lab.root,
        existing=True,
    )

    if actual_server != lab.server:
        raise RuntimeError(
            'restored server root differs from lab server path'
        )

    return clone


def write_backup_restore_proofs(
    manifest,
    output,
    lab,
    client_output,
    server_pid,
    client_pid,
    before_status,
    recovery_point,
    snapshot_identity,
    clone_identity,
):
    if lab.active:
        raise RuntimeError(
            'backup/restore proofs require stopped functional server'
        )

    before_path = output / 'backup-before.json'
    maintenance_path = output / 'pre-maintenance-backup.json'
    snapshot_path = output / 'backup-snapshot-identity.json'
    clone_path = output / 'restore-clone-identity.json'

    result_path = client_output / 'result.json'
    heartbeat_path = client_output / 'heartbeat.json'
    launcher_log = client_output / 'launcher.log'

    result = json.loads(
        result_path.read_text()
    )

    heartbeat = json.loads(
        heartbeat_path.read_text()
    )

    if result != {
        'result': 'PASS',
    }:
        raise RuntimeError(
            'restored-world client probe did not produce PASS'
        )

    elapsed = heartbeat.get(
        'elapsed_seconds'
    )

    if (
        not isinstance(
            heartbeat.get('connected'),
            bool,
        )
        or not isinstance(
            elapsed,
            (int, float),
        )
        or isinstance(
            elapsed,
            bool,
        )
        or not math.isfinite(
            elapsed
        )
        or elapsed <= 0
    ):
        raise RuntimeError(
            'restored-world client heartbeat is malformed'
        )

    previous_point = require_healthy_status(
        before_status
    )

    backup_receipt = output / 'backup.json'
    backup_receipt.write_text(
        json.dumps(
            {
                'result': 'PASS',
                'previous_snapshot_uuid': (
                    previous_point['snapshot_uuid']
                ),
                'snapshot_path': (
                    recovery_point['snapshot_path']
                ),
                'snapshot_uuid': (
                    recovery_point['snapshot_uuid']
                ),
                'filesystem_uuid': (
                    recovery_point['filesystem_uuid']
                ),
                'created_at': (
                    recovery_point['created_at']
                ),
                'readonly': (
                    snapshot_identity['readonly']
                ),
                'verified_subvolume_uuid': (
                    snapshot_identity['subvolume_uuid']
                ),
            },
            indent=2,
        )
        + '\n'
    )

    dh_receipt_path = output / 'restore-dh.json'
    dh_receipt = json.loads(dh_receipt_path.read_text())
    if dh_receipt.get('result') != 'PASS':
        raise RuntimeError('restored DH data path did not pass')

    restore_receipt = output / 'restore.json'
    restore_receipt.write_text(
        json.dumps(
            {
                'result': 'PASS',
                'source_snapshot_path': (
                    snapshot_identity['path']
                ),
                'source_snapshot_uuid': (
                    snapshot_identity['subvolume_uuid']
                ),
                'restore_clone_path': (
                    clone_identity['path']
                ),
                'restore_clone_uuid': (
                    clone_identity['subvolume_uuid']
                ),
                'restore_clone_parent_uuid': (
                    clone_identity['parent_uuid']
                ),
                'dh_subtest': dh_receipt,
                'client_probe_result': result,
                'final_heartbeat': heartbeat,
                'server_pid': server_pid,
                'client_pid': client_pid,
                'server_world': str(
                    lab.server
                ),
                'baseline_uuid': (
                    manifest['baseline']['subvolume_uuid']
                ),
            },
            indent=2,
        )
        + '\n'
    )

    immutable = [
        before_path,
        maintenance_path,
        snapshot_path,
        clone_path,
        backup_receipt,
        restore_receipt,
        result_path,
        heartbeat_path,
        launcher_log,
        lab.log,
    ]

    for path in immutable:
        path.chmod(
            0o400
        )

    backup_evidence = [
        (backup_receipt, 'json'),
        (before_path, 'json'),
        (maintenance_path, 'json'),
        (snapshot_path, 'json'),
    ]

    restore_evidence = [
        (restore_receipt, 'json'),
        (snapshot_path, 'json'),
        (clone_path, 'json'),
        (result_path, 'json'),
        (heartbeat_path, 'json'),
        (launcher_log, 'log'),
        (lab.log, 'log'),
    ]

    restore_evidence.append((dh_receipt_path, 'json'))
    restore_evidence.extend((Path(entry['path']), entry['type']) for entry in dh_receipt['evidence'])

    references = {
        'backup': write_proof(
            manifest,
            'backup',
            output / 'backup-proof.json',
            backup_evidence,
            'PASS',
        ),
        'restore': write_proof(
            manifest,
            'restore',
            output / 'restore-proof.json',
            restore_evidence,
            'PASS',
        ),
    }

    reference_path = (
        output
        / 'backup-restore-reference.json'
    )

    reference_path.write_bytes(
        canonical_bytes(
            references
        )
    )
    reference_path.chmod(
        0o400
    )

    return references


def inspect_restored_server_dh(lab, output):
    if lab.active:
        raise RuntimeError('restored DH snapshot must be inspected before server boot')
    sources = sorted(lab.server.rglob('DistantHorizons.sqlite'))
    if not sources:
        raise RuntimeError('restored server has no DH database')
    databases = [inspect_closed_database(source, output / f'server-dh-{index}.sqlite',
                 owner_stopped=True, require_useful=False) for index, source in enumerate(sources)]
    useful_rows = sum(database['useful_full_data_rows'] for database in databases)
    if useful_rows <= 0:
        raise RuntimeError('restored snapshot contains no useful DH data before boot')
    summary = {'inspected_before_server_boot': True, 'database_count': len(databases),
               'useful_database_count': sum(database['useful_full_data_rows'] > 0 for database in databases),
               'aggregate_useful_full_data_rows': useful_rows, 'databases': databases}
    path = output / 'restore-server-dh.json'
    path.write_bytes(canonical_bytes(summary))
    path.chmod(0o400)
    return summary


def exercise_restored_dh(lab, manifest, output, restored_summary):
    if restored_summary.get('inspected_before_server_boot') is not True or restored_summary.get('aggregate_useful_full_data_rows', 0) <= 0:
        raise RuntimeError('restored DH client requires useful snapshot data inspected before boot')
    dh_output = lab.output / 'client-restore-dh'
    with Client(manifest, dh_output, 'dh-clean', 60, fresh_cache=True) as client:
        exercise_dh_client(lab, client)
        dh_pid = client.pid
    result = json.loads((dh_output / 'result.json').read_text())
    heartbeat = json.loads((dh_output / 'heartbeat.json').read_text())
    elapsed = heartbeat.get('elapsed_seconds')
    if result != {'result': 'PASS'} or not isinstance(heartbeat.get('connected'), bool) or isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed <= 0:
        raise RuntimeError('restored DH client completion evidence is malformed')
    messages = read_dh_messages(dh_output / 'dh-received.jsonl')
    if dh_outcome(messages, manifest) != 'PASS' or not any(
        message['type'] in ('FullDataSourceResponseMessage', 'FullDataSplitMessage')
        and not message['exception_type'] for message in messages
    ):
        raise RuntimeError('restored DH client received no useful full-data response')
    client_databases = inspect_closed_cache(
        Path(manifest['client']['root']) / 'instances/dh-clean/minecraft/Distant_Horizons_server_data',
        dh_output, owner_stopped=not Path(f'/proc/{dh_pid}').exists())
    dh_evidence = [{'path': str(dh_output / filename), 'type': kind}
                   for filename, kind in (('result.json', 'json'), ('heartbeat.json', 'json'),
                                          ('dh-received.jsonl', 'log'), ('launcher.log', 'log'))]
    dh_evidence.extend({'path': database['copy'], 'type': 'sqlite'}
                       for database in restored_summary['databases'] + client_databases)
    dh_evidence.append({'path': str(output / 'restore-server-dh.json'), 'type': 'json'})
    dh_receipt = {'result': 'PASS', 'server_databases': restored_summary['databases'],
                  'preboot_server_data': restored_summary,
                  'client_databases': client_databases, 'client_pid': dh_pid,
                  'message_count': len(messages), 'evidence': dh_evidence}
    (output / 'restore-dh.json').write_bytes(canonical_bytes(dh_receipt))
    (output / 'restore-dh.json').chmod(0o400)
    return dh_receipt


def execute(
    manifest,
    output,
):
    validate_candidate(
        manifest,
        HERE.parent.parent,
    )

    if 'client' not in manifest:
        raise ValueError(
            'backup/restore qualification requires client identity'
        )

    output = prepare_output(
        output
    )

    candidate_path = (
        output
        / 'candidate-manifest.json'
    )

    candidate_path.write_bytes(
        canonical_bytes(
            manifest
        )
    )
    candidate_path.chmod(
        0o400
    )

    before_status = json.loads(
        command(
            'minecraft-backup',
            'status',
            '--live',
        )
    )

    require_healthy_status(
        before_status
    )

    before_path = (
        output
        / 'backup-before.json'
    )

    before_path.write_bytes(
        canonical_bytes(
            before_status
        )
    )
    before_path.chmod(
        0o400
    )

    lab = None

    try:
        maintenance.enter(
            output
        )

        maintenance_path = (
            output
            / 'pre-maintenance-backup.json'
        )

        after_status = json.loads(
            maintenance_path.read_text()
        )

        recovery_point = require_fresh_backup(
            before_status,
            after_status,
        )

        snapshot_identity = verify_recovery_point(
            recovery_point
        )

        snapshot_identity_path = (
            output
            / 'backup-snapshot-identity.json'
        )

        snapshot_identity_path.write_bytes(
            canonical_bytes(
                snapshot_identity
            )
        )
        snapshot_identity_path.chmod(
            0o400
        )

        lab_output = Path(
            str(output)
            + '-restore-lab'
        )

        if lab_output.exists():
            raise RuntimeError(
                'restore lab output already exists'
            )

        lab = Lab(
            manifest,
            lab_output,
        )

        clone_identity = (
            replace_lab_root_with_snapshot(
                lab,
                snapshot_identity,
            )
        )

        clone_identity_path = (
            output
            / 'restore-clone-identity.json'
        )

        clone_identity_path.write_bytes(
            canonical_bytes(
                clone_identity
            )
        )
        clone_identity_path.chmod(
            0o400
        )

        restored_summary = inspect_restored_server_dh(lab, output)

        with lab:
            lab.start()

            client_output = (
                lab_output
                / 'client-restore'
            )

            with Client(
                manifest,
                client_output,
                'no-dh',
                45,
            ) as client:
                exercise_non_dh_client(
                    lab,
                    client,
                )

                client_pid = client.pid

            server_pid = lab.pid
            exercise_restored_dh(lab, manifest, output, restored_summary)

        return write_backup_restore_proofs(
            manifest,
            output,
            lab,
            client_output,
            server_pid,
            client_pid,
            before_status,
            recovery_point,
            snapshot_identity,
            clone_identity,
        )

    finally:
        try:
            if lab is not None:
                lab.stop()
        finally:
            if (
                output
                / 'maintenance.json'
            ).exists():
                maintenance.restore(
                    output
                )

                if (
                    output
                    / 'guard-armed'
                ).exists():
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
        parser.error(
            'root required'
        )

    os.umask(
        0o077
    )

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

    print(
        json.dumps(
            execute(
                manifest,
                args.output,
            )
        )
    )
