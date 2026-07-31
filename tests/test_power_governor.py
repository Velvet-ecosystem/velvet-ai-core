"""Tests for recommendation-only power-aware scheduling."""

import unittest

from velvet.core.power_governor import (
    PowerDisposition,
    PowerGovernor,
    PowerState,
    WorkloadClass,
    WorkloadRequest,
)


class PowerGovernorTests(unittest.TestCase):
    def setUp(self):
        self.governor = PowerGovernor()

    def state(self, **changes):
        values = {
            "ignition_on": True,
            "battery_voltage": 13.8,
            "charging": True,
            "temperature_c": 45.0,
            "node_healthy": True,
            "owner_present": True,
            "runtime_mode": "parked",
        }
        values.update(changes)
        return PowerState(**values)

    def test_protected_work_survives_low_power(self):
        decision = self.governor.decide(
            WorkloadRequest("receipts", WorkloadClass.PROTECTED),
            self.state(
                ignition_on=False,
                charging=False,
                battery_voltage=10.8,
            ),
        )
        self.assertEqual(decision.disposition, PowerDisposition.RUN)
        self.assertFalse(decision.authority_granted)
        self.assertFalse(decision.execution_performed)

    def test_yield_first_pauses_before_protected_work(self):
        decision = self.governor.decide(
            WorkloadRequest("archive-index", WorkloadClass.YIELD_FIRST),
            self.state(
                ignition_on=False,
                charging=False,
                battery_voltage=11.5,
            ),
        )
        self.assertEqual(decision.disposition, PowerDisposition.PAUSE)

    def test_degradable_work_reduces_under_heat(self):
        decision = self.governor.decide(
            WorkloadRequest("voice", WorkloadClass.DEGRADABLE),
            self.state(temperature_c=82.0),
        )
        self.assertEqual(decision.disposition, PowerDisposition.DEGRADE)

    def test_unhealthy_node_refuses_new_work(self):
        decision = self.governor.decide(
            WorkloadRequest("ui", WorkloadClass.DEGRADABLE),
            self.state(node_healthy=False),
        )
        self.assertEqual(decision.disposition, PowerDisposition.REFUSE)

    def test_disallowed_driving_work_pauses(self):
        decision = self.governor.decide(
            WorkloadRequest(
                "model-experiment",
                WorkloadClass.YIELD_FIRST,
                allow_while_driving=False,
            ),
            self.state(runtime_mode="driving"),
        )
        self.assertEqual(decision.disposition, PowerDisposition.PAUSE)


if __name__ == "__main__":
    unittest.main()
