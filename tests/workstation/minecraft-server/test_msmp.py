#!/usr/bin/env python3

import importlib.util
import json
import os
import unittest
from collections import deque
from pathlib import Path


SOURCE = Path(os.environ["MINECRAFT_MSMP_SOURCE"])
SPEC = importlib.util.spec_from_file_location(
    "minecraft_msmp",
    SOURCE,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SOURCE}")

msmp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(msmp)


def response(request_id, result):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def rpc_error(
    request_id,
    code=-32601,
    message="Method not found",
):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def notification(method):
    return {
        "jsonrpc": "2.0",
        "method": method,
    }


def method_response(results):
    def build(websocket):
        request = websocket.sent[-1]
        return response(
            request["id"],
            results[request["method"]],
        )

    return build


def backup_discovery():
    return {
        "openrpc": "1.3.2",
        "methods": [
            {"name": name}
            for name in sorted(
                msmp.BACKUP_CAPABILITIES
            )
        ],
    }


class FakeWebSocket:
    def __init__(self, incoming):
        self.incoming = deque(incoming)
        self.sent = []

    def send(self, raw):
        self.sent.append(json.loads(raw))

    def recv(self, timeout=None):
        del timeout

        if not self.incoming:
            raise TimeoutError("fake websocket timed out")

        message = self.incoming.popleft()

        if isinstance(message, BaseException):
            raise message

        if callable(message):
            message = message(self)

        if isinstance(message, str):
            return message

        return json.dumps(message)


class MsmpSessionTests(unittest.TestCase):
    def test_call_buffers_notification_before_response(self):
        websocket = FakeWebSocket(
            [
                notification(
                    "minecraft:notification/server/activity"
                ),
                response(1, True),
            ]
        )
        session = msmp.MsmpSession(websocket)

        result = session.call(
            msmp.AUTOSAVE_GET_METHOD,
            timeout=1,
        )

        self.assertIs(
            result,
            True,
        )
        self.assertEqual(
            session.notifications[0]["method"],
            "minecraft:notification/server/activity",
        )

    def test_rpc_error_is_reported(self):
        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    rpc_error(1),
                ]
            )
        )

        with self.assertRaises(msmp.RpcError):
            session.call(
                "minecraft:does_not_exist",
                timeout=1,
            )

    def test_unexpected_response_id_is_protocol_error(self):
        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    response(99, {}),
                ]
            )
        )

        with self.assertRaises(msmp.ProtocolError):
            session.call(
                "minecraft:test",
                timeout=1,
            )

    def test_invalid_json_is_protocol_error(self):
        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    "not-json",
                ]
            )
        )

        with self.assertRaises(msmp.ProtocolError):
            session.call(
                "minecraft:test",
                timeout=1,
            )

    def test_autosave_get_and_set_validate_results(self):
        websocket = FakeWebSocket(
            [
                response(1, True),
                response(2, False),
            ]
        )
        session = msmp.MsmpSession(websocket)

        self.assertTrue(
            session.get_autosave(timeout=1)
        )
        self.assertFalse(
            session.set_autosave(
                False,
                timeout=1,
            )
        )

        self.assertEqual(
            websocket.sent[1]["params"],
            {"enable": False},
        )

    def test_autosave_rejects_object_wrapped_result(self):
        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    response(
                        1,
                        {"enabled": True},
                    ),
                ]
            )
        )

        with self.assertRaises(msmp.ProtocolError):
            session.get_autosave(timeout=1)

    def test_discovery_requires_backup_capabilities(self):
        document = {
            "openrpc": "1.3.2",
            "methods": [
                {"name": name}
                for name in sorted(
                    msmp.BACKUP_CAPABILITIES
                )
            ],
        }

        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    response(1, document),
                ]
            )
        )

        session.require_backup_capabilities(
            timeout=1
        )

    def test_discovery_rejects_missing_capability(self):
        document = {
            "openrpc": "1.3.2",
            "methods": [
                {
                    "name": msmp.SAVE_METHOD,
                },
            ],
        }

        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    response(1, document),
                ]
            )
        )

        with self.assertRaises(msmp.ProtocolError):
            session.require_backup_capabilities(
                timeout=1
            )

    def test_discovery_rejects_malformed_methods_structure(self):
        documents = (
            None,
            [],
            {},
            {"methods": {}},
            {"methods": [None]},
            {"methods": [{}]},
            {"methods": [{"name": 123}]},
            {"methods": [{"name": ""}]},
        )

        for document in documents:
            with self.subTest(document=document):
                with self.assertRaises(
                    msmp.ProtocolError
                ):
                    msmp.discovered_names(document)

    def test_nested_names_do_not_satisfy_discovery_capabilities(self):
        document = {
            "openrpc": "1.3.2",
            "methods": [
                {
                    "name": msmp.SAVE_METHOD,
                },
            ],
            "nested": {
                "fake_methods": [
                    {"name": name}
                    for name in sorted(
                        msmp.BACKUP_CAPABILITIES
                    )
                ],
            },
        }

        self.assertEqual(
            msmp.discovered_names(document),
            {msmp.SAVE_METHOD},
        )

        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    response(1, document),
                ]
            )
        )

        with self.assertRaises(
            msmp.ProtocolError
        ):
            session.require_backup_capabilities(
                timeout=1
            )

    def test_save_waits_for_notifications_after_response(self):
        websocket = FakeWebSocket(
            [
                response(
                    1,
                    True,
                ),
                notification(
                    msmp.SAVING_NOTIFICATION
                ),
                notification(
                    msmp.SAVED_NOTIFICATION
                ),
            ]
        )

        session = msmp.MsmpSession(websocket)
        session.save_and_wait(timeout=1)

        self.assertEqual(
            websocket.sent[0]["method"],
            msmp.SAVE_METHOD,
        )
        self.assertEqual(
            websocket.sent[0]["params"],
            {"flush": True},
        )

    def test_save_handles_notifications_before_response(self):
        websocket = FakeWebSocket(
            [
                notification(
                    msmp.SAVING_NOTIFICATION
                ),
                notification(
                    msmp.SAVED_NOTIFICATION
                ),
                response(
                    1,
                    True,
                ),
            ]
        )

        session = msmp.MsmpSession(websocket)
        session.save_and_wait(timeout=1)

    def test_stale_saved_notification_does_not_satisfy_barrier(self):
        websocket = FakeWebSocket(
            [
                notification(
                    msmp.SAVED_NOTIFICATION
                ),
                response(
                    1,
                    True,
                ),
                notification(
                    msmp.SAVING_NOTIFICATION
                ),
            ]
        )

        session = msmp.MsmpSession(websocket)

        with self.assertRaises(TimeoutError):
            session.save_and_wait(timeout=1)

    def test_save_rejects_object_wrapped_result(self):
        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    response(
                        1,
                        {"saving": True},
                    ),
                ]
            )
        )

        with self.assertRaises(msmp.ProtocolError):
            session.save_and_wait(timeout=1)

    def test_save_rejects_unaccepted_result(self):
        session = msmp.MsmpSession(
            FakeWebSocket(
                [
                    response(
                        1,
                        False,
                    ),
                ]
            )
        )

        with self.assertRaises(msmp.ProtocolError):
            session.save_and_wait(timeout=1)


class BackupTransactionTests(unittest.TestCase):
    def test_transaction_restores_enabled_autosave(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, False),
                response(4, False),
                response(5, True),
                notification(msmp.SAVING_NOTIFICATION),
                notification(msmp.SAVED_NOTIFICATION),
                response(6, True),
            ]
        )
        session = msmp.MsmpSession(websocket)
        actions = []

        result = msmp.run_backup_transaction(
            session,
            lambda: actions.append("snapshot") or "snapshot-result",
            rpc_timeout=1,
            save_timeout=1,
        )

        self.assertEqual(result, "snapshot-result")
        self.assertEqual(actions, ["snapshot"])
        self.assertEqual(
            [request["method"] for request in websocket.sent],
            [
                "rpc.discover",
                msmp.AUTOSAVE_GET_METHOD,
                msmp.AUTOSAVE_SET_METHOD,
                msmp.AUTOSAVE_GET_METHOD,
                msmp.SAVE_METHOD,
                msmp.AUTOSAVE_SET_METHOD,
            ],
        )
        self.assertEqual(
            websocket.sent[2]["params"],
            {"enable": False},
        )
        self.assertEqual(
            websocket.sent[5]["params"],
            {"enable": True},
        )

    def test_transaction_preserves_disabled_autosave(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, False),
                response(3, False),
                response(4, True),
                notification(msmp.SAVING_NOTIFICATION),
                notification(msmp.SAVED_NOTIFICATION),
            ]
        )
        session = msmp.MsmpSession(websocket)

        msmp.run_backup_transaction(
            session,
            lambda: None,
            rpc_timeout=1,
            save_timeout=1,
        )

        self.assertEqual(
            [request["method"] for request in websocket.sent],
            [
                "rpc.discover",
                msmp.AUTOSAVE_GET_METHOD,
                msmp.AUTOSAVE_GET_METHOD,
                msmp.SAVE_METHOD,
            ],
        )

    def test_action_failure_restores_autosave(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, False),
                response(4, False),
                response(5, True),
                notification(msmp.SAVING_NOTIFICATION),
                notification(msmp.SAVED_NOTIFICATION),
                response(6, True),
            ]
        )
        session = msmp.MsmpSession(websocket)

        def fail_action():
            raise RuntimeError("snapshot failed")

        with self.assertRaisesRegex(
            RuntimeError,
            "snapshot failed",
        ):
            msmp.run_backup_transaction(
                session,
                fail_action,
                rpc_timeout=1,
                save_timeout=1,
            )

        self.assertEqual(
            websocket.sent[-1]["method"],
            msmp.AUTOSAVE_SET_METHOD,
        )
        self.assertEqual(
            websocket.sent[-1]["params"],
            {"enable": True},
        )

    def test_save_failure_restores_autosave(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, False),
                response(4, False),
                response(5, False),
                response(6, True),
            ]
        )
        session = msmp.MsmpSession(websocket)
        action_called = []

        with self.assertRaises(msmp.ProtocolError):
            msmp.run_backup_transaction(
                session,
                lambda: action_called.append(True),
                rpc_timeout=1,
                save_timeout=1,
            )

        self.assertEqual(action_called, [])
        self.assertEqual(
            websocket.sent[-1]["params"],
            {"enable": True},
        )

    def test_failed_disable_still_attempts_restore(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, True),
                response(4, True),
            ]
        )
        session = msmp.MsmpSession(websocket)

        with self.assertRaises(msmp.ProtocolError):
            msmp.run_backup_transaction(
                session,
                lambda: None,
                rpc_timeout=1,
                save_timeout=1,
            )

        self.assertEqual(
            websocket.sent[-1]["method"],
            msmp.AUTOSAVE_SET_METHOD,
        )
        self.assertEqual(
            websocket.sent[-1]["params"],
            {"enable": True},
        )

    def test_restore_failure_after_success_is_fatal(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, False),
                response(4, False),
                response(5, True),
                notification(msmp.SAVING_NOTIFICATION),
                notification(msmp.SAVED_NOTIFICATION),
                response(6, False),
            ]
        )
        session = msmp.MsmpSession(websocket)

        with self.assertRaises(msmp.BackupTransactionError) as context:
            msmp.run_backup_transaction(
                session,
                lambda: None,
                rpc_timeout=1,
                save_timeout=1,
            )

        self.assertIsNone(context.exception.primary_error)
        self.assertIsInstance(
            context.exception.restore_error,
            msmp.ProtocolError,
        )

    def test_primary_and_restore_failures_are_both_preserved(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, False),
                response(4, False),
                response(5, True),
                notification(msmp.SAVING_NOTIFICATION),
                notification(msmp.SAVED_NOTIFICATION),
                response(6, False),
            ]
        )
        session = msmp.MsmpSession(websocket)

        def fail_action():
            raise RuntimeError("snapshot failed")

        with self.assertRaises(msmp.BackupTransactionError) as context:
            msmp.run_backup_transaction(
                session,
                fail_action,
                rpc_timeout=1,
                save_timeout=1,
            )

        self.assertIsInstance(
            context.exception.primary_error,
            RuntimeError,
        )
        self.assertIsInstance(
            context.exception.restore_error,
            msmp.ProtocolError,
        )


    def test_unread_stale_save_pair_does_not_satisfy_new_barrier(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, False),

                # A complete old save pair is already unread on the
                # WebSocket when the barrier fence begins.
                notification(
                    msmp.SAVING_NOTIFICATION
                ),
                notification(
                    msmp.SAVED_NOTIFICATION
                ),

                # With the hardened implementation this is the fence
                # autosave query and must report autosave disabled.
                # Without the fence, this dynamically becomes the SAVE
                # response and reports success, allowing the stale pair
                # to falsely satisfy the old implementation.
                method_response(
                    {
                        msmp.AUTOSAVE_GET_METHOD: False,
                        msmp.SAVE_METHOD: True,
                    }
                ),

                # Response for the real flushed save in the hardened
                # implementation.
                response(5, True),

                # The new save starts but deliberately never completes.
                notification(
                    msmp.SAVING_NOTIFICATION
                ),
                TimeoutError(
                    "new save completion notification missing"
                ),

                # Autosave restoration after the primary timeout.
                response(6, True),
            ]
        )

        session = msmp.MsmpSession(websocket)
        action_called = []

        with self.assertRaisesRegex(
            TimeoutError,
            "new save completion notification missing",
        ):
            msmp.run_backup_transaction(
                session,
                lambda: action_called.append(True),
                rpc_timeout=1,
                save_timeout=1,
            )

        self.assertEqual(
            action_called,
            [],
        )
        self.assertEqual(
            [request["method"] for request in websocket.sent],
            [
                "rpc.discover",
                msmp.AUTOSAVE_GET_METHOD,
                msmp.AUTOSAVE_SET_METHOD,
                msmp.AUTOSAVE_GET_METHOD,
                msmp.SAVE_METHOD,
                msmp.AUTOSAVE_SET_METHOD,
            ],
        )

    def test_backup_hooks_bracket_autosave_changes(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, False),
                response(4, False),
                response(5, True),
                notification(msmp.SAVING_NOTIFICATION),
                notification(msmp.SAVED_NOTIFICATION),
                response(6, True),
            ]
        )
        session = msmp.MsmpSession(websocket)
        events = []

        def before_disable():
            events.append(
                ("before-disable", len(websocket.sent))
            )

        def after_restore():
            events.append(
                ("after-restore", len(websocket.sent))
            )

        msmp.run_backup_transaction(
            session,
            lambda: None,
            rpc_timeout=1,
            save_timeout=1,
            before_autosave_disable=before_disable,
            after_autosave_restore=after_restore,
        )

        self.assertEqual(
            events,
            [
                ("before-disable", 2),
                ("after-restore", 6),
            ],
        )
        self.assertEqual(
            websocket.sent[2]["params"],
            {"enable": False},
        )
        self.assertEqual(
            websocket.sent[5]["params"],
            {"enable": True},
        )

    def test_backup_hooks_are_unused_when_autosave_was_disabled(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, False),
                response(3, False),
                response(4, True),
                notification(msmp.SAVING_NOTIFICATION),
                notification(msmp.SAVED_NOTIFICATION),
            ]
        )
        session = msmp.MsmpSession(websocket)
        events = []

        msmp.run_backup_transaction(
            session,
            lambda: None,
            rpc_timeout=1,
            save_timeout=1,
            before_autosave_disable=lambda: events.append("before"),
            after_autosave_restore=lambda: events.append("after"),
        )

        self.assertEqual(events, [])
        self.assertEqual(
            [request["method"] for request in websocket.sent],
            [
                "rpc.discover",
                msmp.AUTOSAVE_GET_METHOD,
                msmp.AUTOSAVE_GET_METHOD,
                msmp.SAVE_METHOD,
            ],
        )

    def test_failed_before_disable_hook_sends_no_autosave_update(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
            ]
        )
        session = msmp.MsmpSession(websocket)
        action_called = []

        def fail_before_disable():
            raise RuntimeError("marker creation failed")

        with self.assertRaisesRegex(
            RuntimeError,
            "marker creation failed",
        ):
            msmp.run_backup_transaction(
                session,
                lambda: action_called.append(True),
                rpc_timeout=1,
                save_timeout=1,
                before_autosave_disable=fail_before_disable,
            )

        self.assertEqual(action_called, [])
        self.assertEqual(
            [request["method"] for request in websocket.sent],
            [
                "rpc.discover",
                msmp.AUTOSAVE_GET_METHOD,
            ],
        )

    def test_failed_after_restore_hook_is_recovery_failure(self):
        websocket = FakeWebSocket(
            [
                response(1, backup_discovery()),
                response(2, True),
                response(3, False),
                response(4, False),
                response(5, True),
                notification(msmp.SAVING_NOTIFICATION),
                notification(msmp.SAVED_NOTIFICATION),
                response(6, True),
            ]
        )
        session = msmp.MsmpSession(websocket)

        def fail_after_restore():
            raise RuntimeError("marker cleanup failed")

        with self.assertRaises(
            msmp.BackupTransactionError
        ) as context:
            msmp.run_backup_transaction(
                session,
                lambda: None,
                rpc_timeout=1,
                save_timeout=1,
                after_autosave_restore=fail_after_restore,
            )

        self.assertIsNone(
            context.exception.primary_error
        )
        self.assertIsInstance(
            context.exception.restore_error,
            RuntimeError,
        )


class ValidationTests(unittest.TestCase):
    def test_custom_paths_and_queries_are_rejected(self):
        secret = (
            "0123456789"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcd"
        )

        old_secret = os.environ.get(
            "MINECRAFT_MANAGEMENT_SECRET"
        )
        old_url = os.environ.get(
            "MINECRAFT_MANAGEMENT_URL"
        )

        try:
            os.environ[
                "MINECRAFT_MANAGEMENT_SECRET"
            ] = secret

            for url in (
                "ws://127.0.0.1:25585/custom",
                "ws://127.0.0.1:25585?query=yes",
                "ws://127.0.0.1:25585/#fragment",
            ):
                os.environ[
                    "MINECRAFT_MANAGEMENT_URL"
                ] = url

                with self.assertRaises(
                    msmp.ConfigurationError
                ):
                    msmp.configuration()

        finally:
            if old_secret is None:
                os.environ.pop(
                    "MINECRAFT_MANAGEMENT_SECRET",
                    None,
                )
            else:
                os.environ[
                    "MINECRAFT_MANAGEMENT_SECRET"
                ] = old_secret

            if old_url is None:
                os.environ.pop(
                    "MINECRAFT_MANAGEMENT_URL",
                    None,
                )
            else:
                os.environ[
                    "MINECRAFT_MANAGEMENT_URL"
                ] = old_url


if __name__ == "__main__":
    unittest.main(verbosity=2)
