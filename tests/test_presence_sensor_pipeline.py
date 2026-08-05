import unittest

from velvet.core.presence_fusion import PresencePurpose
from velvet.core.presence_sensor_pipeline import fuse_sensor_packets


class PresenceSensorPipelineTests(unittest.TestCase):
    def packet(
        self,
        source,
        *,
        simulated=True,
        timestamp=100.0,
        confidence=0.98,
    ):
        return {
            "module_id": "module-" + source,
            "node_id": "sim-node",
            "timestamp": timestamp,
            "monotonic_time": timestamp,
            "sensor_type": "seat_presence",
            "interface_type": (
                "simulated-body-v1" if simulated else "serial-json"
            ),
            "health_state": "ONLINE",
            "confidence": confidence,
            "payload": {
                "source_id": source,
                "spatial_presence_source": "seat.driver",
                "zone": "driver-seat",
                "living_motion_detected": True,
                "range_confidence": 0.99,
                "identity_claim": "Mister",
                "owner_match_confidence": 0.99,
                "spoofing_risk": 0.0,
                "permitted_purposes": ["access"],
                "simulated": simulated,
            },
            "receipt_id": "receipt-" + source,
            "source_clock": "sim-clock",
            "stale_after_ms": 5000,
            "calibration_version": "sim-v1",
        }

    def test_simulated_presence_never_unlocks_physical_target(self):
        result = fuse_sensor_packets(
            [self.packet("radar"), self.packet("camera")],
            purpose=PresencePurpose.ACCESS,
            zone="driver-seat",
            now=101.0,
        )

        self.assertTrue(result.fusion.source_diversity_met)
        self.assertGreater(result.fusion.confidence, 0.9)
        self.assertFalse(result.physical_unlock_allowed)
        self.assertEqual(
            result.physical_refusal_reason,
            "simulated_presence_cannot_unlock_physical_target",
        )
        self.assertEqual(
            set(result.simulated_contributors),
            {"radar", "camera"},
        )
        self.assertFalse(result.authority_granted)

    def test_receipt_explains_rejected_stale_evidence(self):
        result = fuse_sensor_packets(
            [
                self.packet("radar", timestamp=90.0),
                self.packet("camera", timestamp=90.0),
            ],
            purpose=PresencePurpose.ACCESS,
            zone="driver-seat",
            now=101.0,
        )

        payload = result.receipt_envelope["payload"]
        self.assertEqual(
            result.receipt_envelope["event_type"],
            "PRESENCE_FUSION_REJECTED",
        )
        self.assertIn(("radar", "stale"), payload["rejected_sources"])
        self.assertEqual(
            payload["input_receipt_ids"],
            ("receipt-radar", "receipt-camera"),
        )


if __name__ == "__main__":
    unittest.main()
