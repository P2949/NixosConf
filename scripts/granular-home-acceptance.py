"""Require consecutive verified physical home boots before arming var."""
import datetime
import json
import os
from pathlib import Path


def require_home_acceptance(records, current_boot, current_system):
    ordered = []
    for record in records:
        when = datetime.datetime.fromisoformat(record["verified_at"])
        if when.tzinfo is None or record["mode"] not in (
            "home", "home-recovery", "normal", "recovery"
        ):
            raise ValueError("Invalid physical acceptance receipt.")
        if not record["verified_boot_id"] or record["verified_boot_id"] == record["boot_id"]:
            raise ValueError("Receipt does not prove a different physical boot.")
        ordered.append((when, record))
    ordered.sort(key=lambda item: item[0])
    if not ordered:
        raise ValueError("No verified physical home boot receipts.")
    latest = ordered[-1][1]
    if latest["verified_boot_id"] != current_boot or latest["system"] != current_system:
        raise ValueError("The current boot and exact running closure are not accepted.")
    boots = set()
    for _, record in reversed(ordered):
        # The initial legacy-home cutover is stage 22, not either repeated
        # root-local-home reset cycle required by stage 23. Old receipts that
        # omit source topology cannot prove those cycles either.
        if record["mode"] != "home" or record.get("seeded_home_fsroot") != "/@root":
            break
        boots.add(record["verified_boot_id"])
    if len(boots) < 2:
        raise ValueError("Var cutover requires two consecutive verified normal reboot cycles from root-local home.")
    return len(boots)


def main():
    if os.geteuid() != 0:
        raise SystemExit("Run the home acceptance guard as root.")
    evidence = Path("/persist/granular-migration")
    try:
        if (evidence / "physical-boot-pending.json").exists():
            raise ValueError("A physical boot check is still pending.")
        records = [json.loads(path.read_text()) for path in evidence.glob("physical-boot-passed-*.json")]
        count = require_home_acceptance(
            records,
            Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            str(Path("/run/current-system").resolve()),
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit("Home acceptance incomplete; var remains unarmed: " + str(error)) from error
    print(f"Home acceptance passed: {count} consecutive verified normal boots.")


if __name__ == "__main__":
    main()
