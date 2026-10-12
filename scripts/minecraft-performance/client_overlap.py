"""Safe client classification; retain PID and reason, never process arguments."""

from pathlib import Path

CLIENT_MAIN_CLASSES = {
    b'net.minecraft.client.main.Main', b'net.fabricmc.loader.impl.launch.knot.KnotClient',
    b'net.fabricmc.loader.launch.knot.KnotClient', b'org.multimc.EntryPoint',
    b'org.prismlauncher.EntryPoint',
}


def minecraft_clients(*, excluded_group=None, proc=Path('/proc')):
    found = []
    for process in proc.iterdir():
        if not process.name.isdigit():
            continue
        try:
            if (process / 'comm').read_text().strip() not in ('java', 'javaw'):
                continue
            if excluded_group is not None:
                groups = (process / 'cgroup').read_text().splitlines()
                if any(line == '0::' + excluded_group or
                       line.startswith('0::' + excluded_group + '/') for line in groups):
                    continue
            # Only compare known main-class tokens in memory. Never retain or
            # report raw cmdline, which can contain account credentials.
            tokens = (process / 'cmdline').read_bytes().split(b'\0')
            reason = 'client_main_class' if CLIENT_MAIN_CLASSES.intersection(tokens) else None
            if reason is None:
                cwd = str((process / 'cwd').resolve())
                if '/PrismLauncher/instances/' in cwd or '/minecraft-performance-client-' in cwd:
                    reason = 'client_instance_directory'
            if reason:
                found.append({'pid': int(process.name), 'reason': reason})
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return found
