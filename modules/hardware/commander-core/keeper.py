import argparse
import glob
import math
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from liquidctl.driver import find_liquidctl_devices
from liquidctl.driver.commander_core import CommanderCore, _CMD_WAKE


HEARTBEAT = Path("/run/commander-core.lastwake")
STATE = Path("/run/commander-core.state")

running = True


def handle_signal(signum, frame):
    global running
    running = False


def sd_notify(message):
    """
    Send a notification to systemd without requiring python-systemd.
    """
    address = os.environ.get("NOTIFY_SOCKET")

    if not address:
        return

    if address.startswith("@"):
        address = "\0" + address[1:]

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(address)
            sock.sendall(message.encode())
    except OSError:
        # Cooling control must not fail merely because status notification
        # failed.
        pass


def find_cpu_package_sensor():
    for hwmon in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            name = Path(hwmon, "name").read_text().strip()
        except OSError:
            continue

        if name != "coretemp":
            continue

        for label_path in glob.glob(f"{hwmon}/temp*_label"):
            try:
                label = Path(label_path).read_text().strip()
            except OSError:
                continue

            if label == "Package id 0":
                input_path = label_path.replace("_label", "_input")

                if os.path.exists(input_path):
                    return Path(input_path)

    raise RuntimeError("could not find coretemp Package id 0 sensor")


def read_temp_c(path):
    return int(path.read_text().strip()) / 1000.0


def write_atomic(path, text):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def write_state(
    status,
    *,
    cpu_temp=None,
    fan_mode=None,
    fan_duty=None,
    pump_duty=None,
    last_wake=None,
    error=None,
):
    lines = [
        f"status={status}",
        f"pid={os.getpid()}",
    ]

    if cpu_temp is not None:
        lines.append(f"cpu_package_temp={cpu_temp:.1f}")

    if fan_mode is not None:
        lines.append(f"fan_mode={fan_mode}")

    if fan_duty is not None:
        lines.append(f"fan_duty={fan_duty}")

    if pump_duty is not None:
        lines.append(f"pump_duty={pump_duty}")

    if last_wake is not None:
        lines.append(f"last_wake_epoch={int(last_wake)}")

    if error is not None:
        lines.append(f"error={error!r}")

    write_atomic(STATE, "\n".join(lines) + "\n")


def update_heartbeat():
    now = time.time()
    write_atomic(HEARTBEAT, f"{int(now)}\n")
    return now


def parse_args(argv=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("--base-fan-duty", type=int, required=True)
    parser.add_argument("--high-fan-duty", type=int, required=True)
    parser.add_argument("--pump-duty", type=int, required=True)

    parser.add_argument("--high-temp", type=float, required=True)
    parser.add_argument("--low-temp", type=float, required=True)

    parser.add_argument("--high-delay", type=float, required=True)
    parser.add_argument("--low-delay", type=float, required=True)

    parser.add_argument("--temp-interval", type=float, required=True)
    parser.add_argument("--wake-interval", type=float, required=True)
    parser.add_argument("--reset-delay", type=float, required=True)

    parser.add_argument("--usbreset", required=True)

    parser.add_argument(
        "--usb-id",
        required=True,
    )

    parser.add_argument(
        "--usb-serial",
        required=True,
    )

    parser.add_argument("--watchdog-seconds", type=float, required=True)

    args = parser.parse_args(argv)

    for value, name in (
        (args.base_fan_duty, "base fan duty"),
        (args.high_fan_duty, "high fan duty"),
        (args.pump_duty, "pump duty"),
    ):
        if not 0 <= value <= 100:
            parser.error(f"{name} must be 0..100")

    if args.base_fan_duty > args.high_fan_duty:
        parser.error("--base-fan-duty must be <= --high-fan-duty")

    if not re.fullmatch(r"[0-9a-fA-F]{4}:[0-9a-fA-F]{4}", args.usb_id):
        parser.error("--usb-id must be four hex digits, a colon, and four hex digits")

    if not args.usb_serial.strip():
        parser.error("--usb-serial must contain a non-whitespace device serial")

    if not (0 <= args.low_temp < args.high_temp <= 100):
        parser.error("temperatures must satisfy 0 <= --low-temp < --high-temp <= 100")

    for name in ("temp_interval", "wake_interval", "reset_delay"):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            parser.error(f"--{name.replace('_', '-')} must be finite and positive")

    for name in ("high_delay", "low_delay"):
        value = getattr(args, name)
        if not math.isfinite(value) or value < 0:
            parser.error(f"--{name.replace('_', '-')} must be finite and nonnegative")

    if not math.isfinite(args.watchdog_seconds) or args.watchdog_seconds <= 0:
        parser.error("--watchdog-seconds must be finite and positive")
    if 2 * max(args.temp_interval, args.wake_interval) >= args.watchdog_seconds:
        parser.error(
            "polling and wake intervals require two intervals of watchdog margin"
        )

    return args


def main():
    args = parse_args()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        HEARTBEAT.unlink(missing_ok=True)
    except OSError:
        pass

    write_state("starting")
    sd_notify("STATUS=Waiting for Commander Core")

    dev = None

    try:
        temp_path = find_cpu_package_sensor()

        print(f"CPU package sensor: {temp_path}", flush=True)

        # Reset the exact physical Commander Core by serial number rather
        # than depending on bus/device or hidraw numbering.
        result = subprocess.run(
            [
                args.usbreset,
                f"SN:{args.usb_serial}",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        print(result.stdout.strip(), flush=True)

        time.sleep(args.reset_delay)

        vid_text, pid_text = args.usb_id.split(":", 1)

        vendor = int(vid_text, 16)
        product = int(pid_text, 16)

        devices = [
            dev
            for dev in find_liquidctl_devices(
                vendor=vendor,
                product=product,
            )
            if isinstance(dev, CommanderCore)
        ]

        if len(devices) != 1:
            raise RuntimeError(
                f"expected exactly one Commander Core, found {len(devices)}"
            )

        dev = devices[0]
        dev.connect()

        # Physical controller:
        #
        # Corsair Commander Core
        # USB 1b1c:0c1c
        # firmware 2.11.221
        #
        # PR #886 currently requires forcing the firmware-v2 code path
        # before set_fixed_speed() in a fresh process.
        dev._fw_major = 2

        dev.set_fixed_speed("pump", args.pump_duty)

        current_duty = args.base_fan_duty
        fan_mode = "base"

        dev.set_fixed_speed("fans", current_duty)

        # Establish firmware-v2 software-control lease immediately.
        dev._send_command(_CMD_WAKE)

        last_wake = time.monotonic()
        heartbeat_time = update_heartbeat()

        hot_since = None
        cool_since = None

        print(
            "Commander Core active: "
            f"fans={current_duty}% "
            f"pump={args.pump_duty}% "
            f"high={args.high_temp:.1f}C/{args.high_delay:g}s "
            f"low={args.low_temp:.1f}C/{args.low_delay:g}s "
            f"wake={args.wake_interval:g}s",
            flush=True,
        )

        sd_notify(
            "READY=1\nSTATUS=Commander Core cooling controller active\nWATCHDOG=1"
        )

        while running:
            loop_start = time.monotonic()

            temp = read_temp_c(temp_path)

            # Temperature state machine.
            if fan_mode == "base":
                cool_since = None

                if temp >= args.high_temp:
                    if hot_since is None:
                        hot_since = loop_start

                    elif loop_start - hot_since >= args.high_delay:
                        current_duty = args.high_fan_duty

                        dev.set_fixed_speed("fans", current_duty)
                        dev._send_command(_CMD_WAKE)

                        fan_mode = "high"
                        hot_since = None

                        last_wake = time.monotonic()
                        heartbeat_time = update_heartbeat()

                        print(
                            f"CPU {temp:.1f}C: switching fans to {current_duty}%",
                            flush=True,
                        )
                else:
                    hot_since = None

            else:
                hot_since = None

                if temp <= args.low_temp:
                    if cool_since is None:
                        cool_since = loop_start

                    elif loop_start - cool_since >= args.low_delay:
                        current_duty = args.base_fan_duty

                        dev.set_fixed_speed("fans", current_duty)
                        dev._send_command(_CMD_WAKE)

                        fan_mode = "base"
                        cool_since = None

                        last_wake = time.monotonic()
                        heartbeat_time = update_heartbeat()

                        print(
                            f"CPU {temp:.1f}C: switching fans to {current_duty}%",
                            flush=True,
                        )
                else:
                    cool_since = None

            # Firmware-v2 software-control keepalive.
            if loop_start - last_wake >= args.wake_interval:
                dev._send_command(_CMD_WAKE)

                last_wake = time.monotonic()
                heartbeat_time = update_heartbeat()

            write_state(
                "active",
                cpu_temp=temp,
                fan_mode=fan_mode,
                fan_duty=current_duty,
                pump_duty=args.pump_duty,
                last_wake=heartbeat_time,
            )

            # Native systemd watchdog replaces the OpenRC healthcheck.
            sd_notify(
                "WATCHDOG=1\n"
                f"STATUS=CPU {temp:.1f}C, "
                f"fans {current_duty}%, pump {args.pump_duty}%"
            )

            elapsed = time.monotonic() - loop_start
            sleep_for = max(0.05, args.temp_interval - elapsed)

            time.sleep(sleep_for)

        sd_notify("STOPPING=1\nSTATUS=Commander Core controller stopping")

        return 0

    except Exception as exc:
        write_state("error", error=exc)

        sd_notify(f"STATUS=Commander Core controller failed: {exc!r}")

        print(
            f"Commander Core controller failed: {exc!r}",
            file=sys.stderr,
            flush=True,
        )

        return 1

    finally:
        try:
            if dev is not None:
                dev.disconnect()
        except Exception:
            pass

        try:
            HEARTBEAT.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
