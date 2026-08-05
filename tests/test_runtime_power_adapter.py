import unittest

from velvet.core.power_governor import (
    PowerDisposition,
    PowerGovernor,
    WorkloadClass,
    WorkloadRequest,
)
from velvet.core.runtime_power_adapter import (
    decide_runtime_power,
    power_decision_payload,
)


class RuntimePowerAdapterTests(unittest.TestCase):
    def test_runtime_payload_drives_governor(self):
        payload = {
            "ignition_on": False,
            "battery_voltage": 11.4,
            "charging": False,
            "temperature_c": 70.0,
            "node_healthy": True,
            "owner_present": False,
            "runtime_mode": "parked",
        }
        decision = decide_runtime_power(
            PowerGovernor(),
            WorkloadRequest(
                "memory.compact",
                WorkloadClass.YIELD_FIRST,
            ),
            payload,
        )
        self.assertEqual(decision.disposition, PowerDisposition.PAUSE)
        wire = power_decision_payload(decision)
        self.assertEqual(wire["disposition"], "PAUSE")
        self.assertFalse(wire["authority_granted"])


if __name__ == "__main__":
    unittest.main()
