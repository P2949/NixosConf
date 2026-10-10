#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
from collections import deque
from pathlib import Path
from time import monotonic
from urllib.parse import urlparse

from websockets.exceptions import WebSocketException
from websockets.sync.client import connect


DEFAULT_URL = "ws://127.0.0.1:25585"
DEFAULT_ENV_FILE = "/persist/secrets/minecraft-management.env"
SECRET_RE = re.compile(r"^[A-Za-z0-9]{40}$")

DEFAULT_RPC_TIMEOUT = 10.0
DEFAULT_SAVE_TIMEOUT = 120.0

SAVE_METHOD = "minecraft:server/save"
AUTOSAVE_GET_METHOD = "minecraft:serversettings/autosave"
AUTOSAVE_SET_METHOD = "minecraft:serversettings/autosave/set"
SAVING_NOTIFICATION = "minecraft:notification/server/saving"
SAVED_NOTIFICATION = "minecraft:notification/server/saved"

BACKUP_CAPABILITIES = {
    SAVE_METHOD,
    AUTOSAVE_GET_METHOD,
    AUTOSAVE_SET_METHOD,
    SAVING_NOTIFICATION,
    SAVED_NOTIFICATION,
}


class ConfigurationError(RuntimeError):
    pass


class ProtocolError(RuntimeError):
    pass


class RpcError(RuntimeError):
    def __init__(self, error):
        self.error = error
        super().__init__(json.dumps(error, sort_keys=True))


class BackupTransactionError(RuntimeError):
    def __init__(self, primary_error, restore_error):
        self.primary_error = primary_error
        self.restore_error = restore_error

        if primary_error is None:
            message = (
                "backup transaction completed its primary action but "
                f"failed to restore autosave: {restore_error}"
            )
        else:
            message = (
                f"backup transaction failed: {primary_error}; "
                f"additionally failed to restore autosave: {restore_error}"
            )

        super().__init__(message)


def fail(message: str) -> None:
    print(f"minecraft-msmp: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_url(url: str) -> str:
    parsed = urlparse(url)

    if parsed.scheme != "ws":
        raise ConfigurationError(
            "management URL must use ws:// because the configured server uses TLS=false"
        )

    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ConfigurationError(
            "management URL must resolve explicitly to a loopback host"
        )

    if parsed.port is None:
        raise ConfigurationError("management URL must contain an explicit port")

    if parsed.username is not None or parsed.password is not None:
        raise ConfigurationError("management URL must not contain credentials")

    if (
        parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ConfigurationError(
            "management URL must not contain a custom path, query, or fragment"
        )

    return url


def read_secret_from_environment_file(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigurationError(
            f"cannot read management environment file {path}: {exc}"
        ) from exc

    secrets = []

    for raw_line in lines:
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if not separator:
            continue

        if key.strip() == "MINECRAFT_MANAGEMENT_SECRET":
            secrets.append(value.strip())

    if len(secrets) != 1:
        raise ConfigurationError(
            "environment file must contain exactly one "
            "MINECRAFT_MANAGEMENT_SECRET assignment"
        )

    return secrets[0]


def load_secret() -> str:
    secret = os.environ.get("MINECRAFT_MANAGEMENT_SECRET")

    if secret is None:
        env_file = Path(
            os.environ.get(
                "MINECRAFT_MANAGEMENT_ENV_FILE",
                DEFAULT_ENV_FILE,
            )
        )
        secret = read_secret_from_environment_file(env_file)

    if SECRET_RE.fullmatch(secret) is None:
        raise ConfigurationError(
            "management secret must be exactly 40 alphanumeric characters"
        )

    return secret


def configuration() -> tuple[str, str]:
    url = validate_url(
        os.environ.get("MINECRAFT_MANAGEMENT_URL", DEFAULT_URL)
    )
    secret = load_secret()
    return url, secret


def open_connection():
    url, secret = configuration()

    return connect(
        url,
        additional_headers={
            "Authorization": f"Bearer {secret}",
        },
        proxy=None,
        compression=None,
        open_timeout=5,
        ping_interval=20,
        ping_timeout=20,
        close_timeout=5,
        max_size=8 * 1024 * 1024,
    )


def remaining(deadline: float) -> float:
    timeout = deadline - monotonic()

    if timeout <= 0:
        raise TimeoutError("operation timed out")

    return timeout


def decode_message(raw) -> dict:
    try:
        message = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProtocolError(f"received invalid JSON: {exc}") from exc

    if not isinstance(message, dict):
        raise ProtocolError("received a non-object JSON-RPC message")

    if message.get("jsonrpc") != "2.0":
        raise ProtocolError("received a message without jsonrpc=2.0")

    return message


def discovered_names(document) -> set[str]:
    if not isinstance(document, dict):
        raise ProtocolError(
            "rpc.discover returned a non-object document"
        )

    methods = document.get("methods")

    if not isinstance(methods, list):
        raise ProtocolError(
            "rpc.discover document is missing a top-level methods array"
        )

    names = set()

    for index, method in enumerate(methods):
        if not isinstance(method, dict):
            raise ProtocolError(
                f"rpc.discover methods[{index}] is not an object"
            )

        name = method.get("name")

        if not isinstance(name, str) or not name:
            raise ProtocolError(
                f"rpc.discover methods[{index}] has no valid name"
            )

        names.add(name)

    return names


class MsmpSession:
    def __init__(self, websocket):
        self.websocket = websocket
        self.next_request_id = 1
        self.notifications = deque()

    def _recv(self, timeout: float | None) -> dict:
        return decode_message(self.websocket.recv(timeout=timeout))

    @staticmethod
    def _notification_method(message: dict) -> str | None:
        if "id" in message:
            return None

        method = message.get("method")

        if isinstance(method, str):
            return method

        return None

    def call(self, method: str, params=None, timeout: float = DEFAULT_RPC_TIMEOUT):
        request_id = self.next_request_id
        self.next_request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }

        if params is not None:
            request["params"] = params

        self.websocket.send(
            json.dumps(
                request,
                separators=(",", ":"),
            )
        )

        deadline = monotonic() + timeout

        while True:
            message = self._recv(remaining(deadline))
            notification_method = self._notification_method(message)

            if notification_method is not None:
                self.notifications.append(message)
                continue

            if message.get("id") != request_id:
                raise ProtocolError(
                    "received an unexpected JSON-RPC response id "
                    f"while waiting for request {request_id}"
                )

            if "error" in message:
                raise RpcError(message["error"])

            if "result" not in message:
                raise ProtocolError(
                    f"JSON-RPC response for {method} has neither result nor error"
                )

            return message["result"]

    def wait_notifications_in_order(
        self,
        methods: list[str],
        timeout: float,
    ) -> None:
        expected = deque(methods)
        deadline = monotonic() + timeout

        while expected:
            if self.notifications:
                message = self.notifications.popleft()
            else:
                message = self._recv(remaining(deadline))

            method = self._notification_method(message)

            if method is None:
                raise ProtocolError(
                    "received an unexpected JSON-RPC response while waiting "
                    "for a server notification"
                )

            if method == expected[0]:
                expected.popleft()

    def clear_notifications(self, methods: set[str]) -> None:
        self.notifications = deque(
            message
            for message in self.notifications
            if self._notification_method(message) not in methods
        )

    def discover(self, timeout: float = DEFAULT_RPC_TIMEOUT):
        return self.call("rpc.discover", timeout=timeout)

    def require_backup_capabilities(self, timeout: float = DEFAULT_RPC_TIMEOUT,
                                    additional_capabilities=()) -> None:
        document = self.discover(timeout=timeout)
        names = discovered_names(document)
        missing = sorted((BACKUP_CAPABILITIES | set(additional_capabilities)) - names)

        if missing:
            raise ProtocolError(
                "server discovery is missing required backup capabilities: "
                + ", ".join(missing)
            )

    def get_autosave(self, timeout: float = DEFAULT_RPC_TIMEOUT) -> bool:
        result = self.call(
            AUTOSAVE_GET_METHOD,
            timeout=timeout,
        )

        if not isinstance(result, bool):
            raise ProtocolError(
                "autosave query returned an unexpected result"
            )

        return result

    def set_autosave(
        self,
        enabled: bool,
        timeout: float = DEFAULT_RPC_TIMEOUT,
    ) -> bool:
        result = self.call(
            AUTOSAVE_SET_METHOD,
            {"enable": enabled},
            timeout=timeout,
        )

        if not isinstance(result, bool):
            raise ProtocolError(
                "autosave update returned an unexpected result"
            )

        if result != enabled:
            raise ProtocolError(
                "autosave update did not reach the requested state"
            )

        return result

    def prepare_backup_save_barrier(
        self,
        timeout: float = DEFAULT_RPC_TIMEOUT,
    ) -> None:
        autosave = self.get_autosave(
            timeout=timeout,
        )

        if autosave:
            raise ProtocolError(
                "autosave is enabled while preparing the backup save barrier"
            )

        # The request/response round trip consumes notifications already
        # unread on the WebSocket. Drop save notifications buffered during
        # that round trip before issuing the new flushed save.
        self.clear_notifications(
            {
                SAVING_NOTIFICATION,
                SAVED_NOTIFICATION,
            }
        )

    def save_and_wait(
        self,
        timeout: float = DEFAULT_SAVE_TIMEOUT,
    ) -> None:
        self.clear_notifications(
            {
                SAVING_NOTIFICATION,
                SAVED_NOTIFICATION,
            }
        )

        deadline = monotonic() + timeout

        result = self.call(
            SAVE_METHOD,
            {"flush": True},
            timeout=remaining(deadline),
        )

        if result is not True:
            raise ProtocolError(
                "flush save was not accepted by the server"
            )

        self.wait_notifications_in_order(
            [
                SAVING_NOTIFICATION,
                SAVED_NOTIFICATION,
            ],
            timeout=remaining(deadline),
        )


def run_backup_transaction(
    session: MsmpSession,
    action,
    rpc_timeout: float = DEFAULT_RPC_TIMEOUT,
    save_timeout: float = DEFAULT_SAVE_TIMEOUT,
    before_autosave_disable=None,
    after_autosave_restore=None,
):
    session.require_backup_capabilities(
        timeout=rpc_timeout,
    )
    original_autosave = session.get_autosave(
        timeout=rpc_timeout,
    )

    primary_error = None
    action_result = None
    restore_required = False

    try:
        if original_autosave:
            if before_autosave_disable is not None:
                before_autosave_disable()

            restore_required = True

            session.set_autosave(
                False,
                timeout=rpc_timeout,
            )

        session.prepare_backup_save_barrier(
            timeout=rpc_timeout,
        )
        session.save_and_wait(
            timeout=save_timeout,
        )
        action_result = action()

    except Exception as exc:
        primary_error = exc

    finally:
        if restore_required:
            try:
                session.set_autosave(
                    True,
                    timeout=rpc_timeout,
                )

                if after_autosave_restore is not None:
                    after_autosave_restore()
            except Exception as restore_error:
                raise BackupTransactionError(
                    primary_error,
                    restore_error,
                ) from restore_error

    if primary_error is not None:
        raise primary_error.with_traceback(
            primary_error.__traceback__
        )

    return action_result


def rpc_call(method: str, params, timeout: float):
    with open_connection() as websocket:
        session = MsmpSession(websocket)
        return session.call(method, params, timeout)


def parse_params(raw: str | None):
    if raw is None:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON params: {exc}")


def operation_error(exc: Exception) -> None:
    if isinstance(exc, RpcError):
        fail(f"JSON-RPC error: {exc}")

    if isinstance(exc, (ConfigurationError, ProtocolError)):
        fail(str(exc))

    if isinstance(exc, (OSError, TimeoutError, WebSocketException)):
        fail(f"management connection failed: {exc}")

    raise exc


def command_validate(_args) -> None:
    try:
        url, _secret = configuration()
    except Exception as exc:
        operation_error(exc)
        return

    print(f"configuration valid: {url}")


def command_discover(args) -> None:
    try:
        result = rpc_call(
            "rpc.discover",
            None,
            args.timeout,
        )
    except Exception as exc:
        operation_error(exc)
        return

    print(json.dumps(result, indent=2, sort_keys=True))


def command_call(args) -> None:
    params = parse_params(args.params)

    try:
        result = rpc_call(
            args.method,
            params,
            args.timeout,
        )
    except Exception as exc:
        operation_error(exc)
        return

    print(json.dumps(result, indent=2, sort_keys=True))


def command_save_and_wait(args) -> None:
    try:
        with open_connection() as websocket:
            session = MsmpSession(websocket)
            session.require_backup_capabilities(
                timeout=args.timeout
            )
            session.save_and_wait(
                timeout=args.timeout
            )
    except Exception as exc:
        operation_error(exc)
        return

    print("flush save completed")


def command_watch(args) -> None:
    try:
        with open_connection() as websocket:
            session = MsmpSession(websocket)

            while True:
                message = session._recv(args.timeout)
                method = session._notification_method(message)

                if method is None:
                    continue

                if args.method is not None and method != args.method:
                    continue

                print(
                    json.dumps(
                        message,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    flush=True,
                )

    except Exception as exc:
        operation_error(exc)


def add_timeout_argument(parser, default) -> None:
    parser.add_argument(
        "--timeout",
        type=float,
        default=default,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="minecraft-msmp",
        description=(
            "Loopback-only client for the Minecraft Server "
            "Management Protocol."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="validate URL and management secret without connecting",
    )
    validate_parser.set_defaults(func=command_validate)

    discover_parser = subparsers.add_parser(
        "discover",
        help="call rpc.discover on the running server",
    )
    add_timeout_argument(discover_parser, DEFAULT_RPC_TIMEOUT)
    discover_parser.set_defaults(func=command_discover)

    call_parser = subparsers.add_parser(
        "call",
        help="perform a JSON-RPC method call",
    )
    call_parser.add_argument("method")
    call_parser.add_argument(
        "params",
        nargs="?",
        help='optional JSON params, e.g. \'{"flush":true}\'',
    )
    add_timeout_argument(call_parser, DEFAULT_RPC_TIMEOUT)
    call_parser.set_defaults(func=command_call)

    save_parser = subparsers.add_parser(
        "save-and-wait",
        help="request a flushed save and wait for save completion",
    )
    add_timeout_argument(save_parser, DEFAULT_SAVE_TIMEOUT)
    save_parser.set_defaults(func=command_save_and_wait)

    watch_parser = subparsers.add_parser(
        "watch",
        help="print server notifications",
    )
    watch_parser.add_argument(
        "method",
        nargs="?",
        help="optional exact notification method to filter",
    )
    add_timeout_argument(watch_parser, None)
    watch_parser.set_defaults(func=command_watch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
