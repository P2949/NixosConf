import importlib.util
import os
import unittest

spec = importlib.util.spec_from_file_location("home_acceptance", os.environ["HOME_ACCEPTANCE_SOURCE"])
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def receipt(index, mode="home", boot=None, system="/nix/store/current-system"):
    return {
        "mode": mode,
        "verified_at": f"2026-10-08T11:{index:02d}:00+00:00",
        "boot_id": f"before-{index}",
        "verified_boot_id": boot or f"after-{index}",
        "system": system,
        "seeded_home_fsroot": "/@root",
    }


class HomeAcceptanceTests(unittest.TestCase):
    def rejected(self, records, boot="after-2", system="/nix/store/current-system"):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            guard.require_home_acceptance(records, boot, system)

    def test_no_or_one_home_boot(self):
        self.rejected([])
        self.rejected([receipt(2)])

    def test_duplicate_receipts_do_not_count_as_distinct_boots(self):
        self.rejected([receipt(1, boot="after-2"), receipt(2)])

    def test_unverified_current_boot_or_wrong_closure(self):
        self.rejected([receipt(1), receipt(2)], boot="unverified")
        self.rejected([receipt(1), receipt(2)], system="/nix/store/other-system")

    def test_recovery_interrupts_consecutive_normal_home_acceptance(self):
        self.rejected([receipt(1), receipt(2, mode="home-recovery"), receipt(3)], boot="after-3")

    def test_latest_recovery_cannot_arm_var(self):
        self.rejected([receipt(1), receipt(2), receipt(3, mode="home-recovery")], boot="after-3")

    def test_wrong_phase_does_not_prove_home_acceptance(self):
        self.rejected([receipt(1, mode="normal"), receipt(2, mode="normal")])

    def test_receipt_order_comes_from_verification_time(self):
        self.assertEqual(guard.require_home_acceptance([receipt(2), receipt(1)], "after-2", "/nix/store/current-system"), 2)

    def test_two_home_boots_after_recovery_are_accepted(self):
        records = [receipt(1, mode="home-recovery"), receipt(2), receipt(3)]
        self.assertEqual(guard.require_home_acceptance(records, "after-3", "/nix/store/current-system"), 2)

    def test_same_boot_cannot_be_a_verified_reboot(self):
        invalid = receipt(1)
        invalid["verified_boot_id"] = invalid["boot_id"]
        self.rejected([invalid, receipt(2)])

    def test_initial_legacy_home_cutover_does_not_count_as_a_repeat_cycle(self):
        initial = receipt(1)
        initial["seeded_home_fsroot"] = "/@home"
        self.rejected([initial, receipt(2)])

    def test_old_receipts_without_source_topology_do_not_count(self):
        old = receipt(1)
        del old["seeded_home_fsroot"]
        self.rejected([old, receipt(2)])

    def test_malformed_receipt_fails_closed(self):
        self.rejected([receipt(1), {}])
        invalid = receipt(1)
        invalid["verified_at"] = "2026-10-08T11:01:00"
        self.rejected([invalid, receipt(2)])


if __name__ == "__main__":
    unittest.main()
