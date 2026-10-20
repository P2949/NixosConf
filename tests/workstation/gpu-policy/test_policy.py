"""Freeze the accepted policy independently of YAML formatting."""

import sys
import unittest

import yaml

GPU = "1002:7550-1025:187A-0000:03:00.0"
CURVE = {30: 0.2, 40: 0.3, 45: 0.5, 50: 0.7, 55: 1.0}
with open(sys.argv.pop(1), encoding="utf-8") as source:
    POLICY = yaml.safe_load(source)


def gpu_config(fan_enabled, static_speed):
    return {
        "fan_control_enabled": fan_enabled,
        "fan_control_settings": {
            "mode": "curve",
            "static_speed": static_speed,
            "temperature_key": "edge",
            "interval_ms": 500,
            "curve": CURVE,
            "spindown_delay_ms": 5000,
            "change_threshold": 2,
        },
        "pmfw_options": {"zero_rpm": True},
        "performance_level": "auto",
    }


class PolicyTests(unittest.TestCase):
    def test_identity_and_selection(self):
        self.assertEqual(POLICY["version"], 7)
        self.assertEqual(set(POLICY["gpus"]), {GPU})
        self.assertEqual(set(POLICY["profiles"]), {"Stock", "Daily"})
        self.assertEqual(POLICY["current_profile"], "Daily")
        self.assertIs(POLICY["auto_switch_profiles"], False)
        for profile in POLICY["profiles"].values():
            self.assertEqual(set(profile), {"gpus"})
            self.assertEqual(set(profile["gpus"]), {GPU})

    def test_stock_is_exact_factory_reference(self):
        stock = POLICY["profiles"]["Stock"]["gpus"][GPU]
        self.assertEqual(stock, POLICY["gpus"][GPU])
        self.assertEqual(stock, gpu_config(False, 0.5))
        self.assertIs(stock["fan_control_enabled"], False)
        self.assertIs(stock["pmfw_options"]["zero_rpm"], True)

    def test_daily_is_exact_validated_policy(self):
        daily = POLICY["profiles"]["Daily"]["gpus"][GPU]
        expected = gpu_config(True, 1.0)
        expected.update(power_cap=238.0, voltage_offset=-150)
        # Full mapping equality also rejects extra core/VRAM clock overrides.
        self.assertEqual(daily, expected)
        self.assertIs(daily["fan_control_enabled"], True)
        self.assertIs(daily["pmfw_options"]["zero_rpm"], True)


if __name__ == "__main__":
    unittest.main()
