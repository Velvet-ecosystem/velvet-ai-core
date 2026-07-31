"""Tests for whole-body saturation scoring."""

import unittest

from velvet.core.saturation import (
    SaturationSample,
    evaluate_saturation,
)


class SaturationTests(unittest.TestCase):
    def test_healthy_samples_pass(self):
        report = evaluate_saturation(
            [
                SaturationSample(
                    timestamp=1,
                    cpu_percent=60,
                    memory_percent=55,
                    receipt_delay_ms=20,
                    disk_latency_ms=12,
                    temperature_c=55,
                ),
                SaturationSample(
                    timestamp=2,
                    cpu_percent=75,
                    memory_percent=62,
                    receipt_delay_ms=30,
                    disk_latency_ms=20,
                    temperature_c=60,
                    recovery_observed=True,
                ),
            ]
        )
        self.assertTrue(report.passed)
        self.assertTrue(report.recovery_observed)

    def test_pressure_breaches_are_named(self):
        report = evaluate_saturation(
            [
                SaturationSample(
                    timestamp=1,
                    cpu_percent=99,
                    memory_percent=95,
                    receipt_delay_ms=500,
                    disk_latency_ms=150,
                    temperature_c=90,
                    dropped_events=2,
                    stale_packets=3,
                    throttled=True,
                    degraded_services=("voice",),
                )
            ]
        )
        self.assertFalse(report.passed)
        self.assertGreaterEqual(len(report.breaches), 8)

    def test_empty_run_is_not_evidence(self):
        with self.assertRaises(ValueError):
            evaluate_saturation([])


if __name__ == "__main__":
    unittest.main()
