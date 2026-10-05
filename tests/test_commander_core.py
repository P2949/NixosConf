import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(os.environ.get("KEEPER_SOURCE", "modules/hardware/commander-core/keeper.py"))
spec = importlib.util.spec_from_file_location("keeper", SOURCE)
keeper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(keeper)


class ArgumentTests(unittest.TestCase):
    def test_current_policy(self):
        args = keeper.parse_args(["--usbreset", "/bin/usbreset"])
        self.assertEqual((args.base_fan_duty, args.high_fan_duty, args.pump_duty), (60, 100, 100))
        self.assertEqual((args.low_temp, args.high_temp), (60, 65))

    def test_reject_invalid_controls_before_hardware_access(self):
        cases = [
            ["--base-fan-duty", "101"], ["--pump-duty", "-1"],
            ["--base-fan-duty", "90", "--high-fan-duty", "80"],
            ["--usb-id", "1b1c:0c1c:abcd"], ["--usb-id", "zzzz:0000"],
            ["--usb-serial", " \t"],
            ["--low-temp", "65"], ["--low-temp", "-1"],
            ["--high-temp", "101"], ["--high-temp", "nan"],
            ["--temp-interval", "0"], ["--wake-interval", "17.5"],
            ["--reset-delay", "-1"], ["--reset-delay", "inf"],
            ["--high-delay", "-1"], ["--low-delay", "nan"],
        ]
        for case in cases:
            with self.subTest(case=case), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    keeper.parse_args(["--usbreset", "/bin/usbreset", *case])
                self.assertEqual(error.exception.code, 2)

    def test_boundary_controls(self):
        args = keeper.parse_args([
            "--usbreset", "/bin/usbreset", "--usb-id", "ABCD:0123",
            "--low-temp", "0", "--high-temp", "100", "--high-delay", "0",
            "--wake-interval", "17.49",
        ])
        self.assertEqual(args.high_delay, 0)


class StateTests(unittest.TestCase):
    def test_temperature_conversion_and_bad_sensor_data(self):
        with tempfile.TemporaryDirectory() as directory:
            sensor = Path(directory, "temp")
            sensor.write_text("65250\n")
            self.assertEqual(keeper.read_temp_c(sensor), 65.25)
            sensor.write_text("unavailable")
            with self.assertRaises(ValueError):
                keeper.read_temp_c(sensor)

    def test_atomic_failure_preserves_previous_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory, "state")
            state.write_text("previous\n")
            with patch.object(keeper.os, "replace", side_effect=OSError("replacement failed")):
                with self.assertRaises(OSError):
                    keeper.write_atomic(state, "new\n")
            self.assertEqual(state.read_text(), "previous\n")

    def test_notify_failure_does_not_stop_cooling(self):
        with patch.dict(os.environ, {"NOTIFY_SOCKET": "/nonexistent/notify-socket"}):
            keeper.sd_notify("WATCHDOG=1")

    def test_hysteresis_and_sensor_failure_cleanup(self):
        class Device:
            def __init__(self):
                self.duties = []
                self.wakes = 0
                self.disconnected = False

            def connect(self):
                pass

            def disconnect(self):
                self.disconnected = True

            def set_fixed_speed(self, channel, duty):
                self.duties.append((channel, duty))

            def _send_command(self, command):
                self.wakes += 1

        device = Device()
        temperatures = [64, 66, 64, 66, 66, 66, 61, 59, 61, 59, 59, 59, 59]
        clock = {"now": 0, "index": 0}

        def sleep(seconds):
            clock["now"] += seconds
            clock["index"] += 1
            if clock["index"] == len(temperatures):
                keeper.running = False

        keeper.running = True
        argv = ["keeper", "--usbreset", "/fake/reset", "--high-delay", "2", "--low-delay", "3", "--wake-interval", "2", "--reset-delay", "0.1"]
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(keeper, "HEARTBEAT", Path(directory, "heartbeat")))
            stack.enter_context(patch.object(keeper, "STATE", Path(directory, "state")))
            stack.enter_context(patch.object(keeper.sys, "argv", argv))
            stack.enter_context(patch.object(keeper.signal, "signal"))
            stack.enter_context(patch.object(keeper, "find_cpu_package_sensor", return_value=Path("/fake/temp")))
            stack.enter_context(patch.object(keeper, "read_temp_c", side_effect=lambda _: temperatures[clock["index"]]))
            stack.enter_context(patch.object(keeper, "CommanderCore", Device))
            stack.enter_context(patch.object(keeper, "find_liquidctl_devices", return_value=[device]))
            reset = stack.enter_context(patch.object(keeper.subprocess, "run"))
            reset.return_value.stdout = "reset simulated"
            stack.enter_context(patch.object(keeper.time, "monotonic", side_effect=lambda: clock["now"]))
            # Reset delay is distinct from the one-second sampling interval.
            stack.enter_context(patch.object(keeper.time, "sleep", side_effect=lambda seconds: None if seconds == 0.1 else sleep(seconds)))
            stack.enter_context(patch.object(keeper, "sd_notify"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            self.assertEqual(keeper.main(), 0)
            self.assertEqual(device.duties, [("pump", 100), ("fans", 60), ("fans", 100), ("fans", 60)])
            self.assertGreater(device.wakes, 3)
            self.assertTrue(device.disconnected)
            self.assertFalse(keeper.HEARTBEAT.exists())

            # A sensor disappearing after startup must fail visibly and release
            # the device/heartbeat rather than leave an apparent healthy lease.
            clock.update(now=0, index=0)
            keeper.running = True
            failed_device = Device()
            keeper.find_liquidctl_devices.return_value = [failed_device]
            keeper.read_temp_c.side_effect = [64, RuntimeError("sensor vanished")]
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(keeper.main(), 1)
            self.assertTrue(failed_device.disconnected)
            self.assertFalse(keeper.HEARTBEAT.exists())
            self.assertIn("status=error\n", keeper.STATE.read_text())
            self.assertIn("sensor vanished", keeper.STATE.read_text())


if __name__ == "__main__":
    unittest.main()
