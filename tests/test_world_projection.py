"""Tests for safe SensorPacket projection into descriptive world state."""

import unittest

from velvet.core.schemas import (
    EntityIdentity,
    EntityLifecycle,
    HealthState,
    IdentityStatus,
    SensorPacket,
    SourceClock,
)
from velvet.core.world_projection import SensorEntityBinding, WorldModelProjector


class WorldProjectionTests(unittest.TestCase):
    def setUp(self):
        self.identity = EntityIdentity(
            entity_id="vehicle:tiburon",
            entity_type="vehicle",
            canonical_name="Tiburon",
            status=IdentityStatus.KNOWN,
            confidence=1.0,
        )
        self.binding = SensorEntityBinding(
            module_id="gnss-1",
            entity_id="vehicle:tiburon",
            state_namespace="position.gnss",
            roles=("vehicle",),
        )
        self.packet = SensorPacket(
            module_id="gnss-1",
            node_id="up2-founder",
            owning_handmaiden="Navigator",
            timestamp=100.0,
            monotonic_time=10.0,
            sensor_type="GNSS",
            interface_type="UART",
            health_state=HealthState.ONLINE,
            confidence=0.95,
            payload={"latitude": 49.0, "longitude": -123.0},
            receipt_id="receipt-gnss-1",
            source_clock=SourceClock.GNSS,
            stale_after_ms=500,
            calibration_version="m9n-1",
        )
        self.projector = WorldModelProjector()

    def test_bound_packet_creates_descriptive_snapshot(self):
        entity = self.projector.project_sensor_packet(
            self.packet,
            self.binding,
            self.identity,
            received_at=100.1,
            now_monotonic=10.2,
            sequence=7,
        )

        self.assertEqual(entity.entity_id, "vehicle:tiburon")
        self.assertEqual(entity.lifecycle, EntityLifecycle.ACTIVE)
        self.assertEqual(entity.temporal.sequence, 7)
        self.assertEqual(
            entity.state["position.gnss"]["payload"]["latitude"],
            49.0,
        )
        self.assertEqual(entity.source_receipt_ids, ("receipt-gnss-1",))
        self.assertFalse(entity.authority_granted)
        self.assertFalse(entity.execution_performed)

    def test_packet_cannot_choose_a_different_entity(self):
        wrong_identity = EntityIdentity(
            entity_id="vehicle:western-star",
            entity_type="vehicle",
            canonical_name="Western Star",
            status=IdentityStatus.KNOWN,
            confidence=1.0,
        )
        with self.assertRaises(ValueError):
            self.projector.project_sensor_packet(
                self.packet,
                self.binding,
                wrong_identity,
                received_at=100.1,
            )

    def test_module_must_match_explicit_binding(self):
        wrong_binding = SensorEntityBinding(
            module_id="other-gnss",
            entity_id="vehicle:tiburon",
            state_namespace="position.gnss",
        )
        with self.assertRaises(ValueError):
            self.projector.project_sensor_packet(
                self.packet,
                wrong_binding,
                self.identity,
                received_at=100.1,
            )

    def test_stale_packet_is_preserved_but_degraded(self):
        entity = self.projector.project_sensor_packet(
            self.packet,
            self.binding,
            self.identity,
            received_at=101.0,
            now_monotonic=10.501,
        )

        self.assertEqual(entity.lifecycle, EntityLifecycle.DEGRADED)
        self.assertTrue(entity.state["position.gnss"]["observation_stale"])
        self.assertEqual(entity.source_receipt_ids, ("receipt-gnss-1",))

    def test_later_packet_preserves_other_state_and_receipt_history(self):
        first = self.projector.project_sensor_packet(
            self.packet,
            self.binding,
            self.identity,
            received_at=100.1,
        )
        second_packet = SensorPacket(
            module_id="voltage-1",
            node_id="up2-founder",
            owning_handmaiden="Ruby",
            timestamp=101.0,
            monotonic_time=11.0,
            sensor_type="VOLTAGE",
            interface_type="ADC",
            health_state=HealthState.DEGRADED,
            confidence=0.8,
            payload={"voltage": 11.6},
            receipt_id="receipt-voltage-1",
            source_clock=SourceClock.DEVICE,
            stale_after_ms=1000,
            calibration_version="bench-1",
            degraded_reason="low voltage",
        )
        second_binding = SensorEntityBinding(
            module_id="voltage-1",
            entity_id="vehicle:tiburon",
            state_namespace="power.voltage",
        )

        second = self.projector.project_sensor_packet(
            second_packet,
            second_binding,
            self.identity,
            received_at=101.1,
            current=first,
        )

        self.assertIn("position.gnss", second.state)
        self.assertIn("power.voltage", second.state)
        self.assertEqual(
            second.source_receipt_ids,
            ("receipt-gnss-1", "receipt-voltage-1"),
        )
        self.assertEqual(second.lifecycle, EntityLifecycle.DEGRADED)

    def test_projection_does_not_infer_spatial_relations(self):
        entity = self.projector.project_sensor_packet(
            self.packet,
            self.binding,
            self.identity,
            received_at=100.1,
        )
        self.assertEqual(entity.spatial_relations, ())


if __name__ == "__main__":
    unittest.main()
