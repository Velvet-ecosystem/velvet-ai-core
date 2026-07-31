"""Tests for the briefing-derived distributed-body foundation contracts."""

import unittest

from velvet.core.module_lifecycle import (
    ModuleLifecycleState,
    standard_lifecycle_contract,
)
from velvet.core.schemas import (
    CapabilityAuthority,
    CapabilityOwnership,
    HealthEvent,
    HealthEventType,
    HealthSeverity,
    HealthState,
    NodeCapabilityManifest,
    SensorPacket,
    SourceClock,
    VehicleInterfaceAuthority,
    VehicleInterfaceContract,
)


class DistributedBodyContractTests(unittest.TestCase):
    def test_sensor_packet_is_stale_and_uses_event_protocol_shape(self):
        packet = SensorPacket(
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
            receipt_id="receipt-sensor-1",
            source_clock=SourceClock.GNSS,
            stale_after_ms=500,
            calibration_version="m9n-1",
        )

        self.assertFalse(packet.is_stale(10.5))
        self.assertTrue(packet.is_stale(10.501))
        record = packet.to_event_protocol()
        self.assertEqual(record["event_type"], "SENSOR_PACKET_OBSERVED")
        self.assertEqual(record["organ_name"], "Navigator")
        self.assertEqual(record["payload"]["receipt_id"], "receipt-sensor-1")

    def test_sensor_packet_rejects_invalid_confidence(self):
        with self.assertRaises(ValueError):
            SensorPacket(
                module_id="seat-1",
                node_id="esp32-seat-1",
                owning_handmaiden="Temperance",
                timestamp=1.0,
                monotonic_time=1.0,
                sensor_type="PRESENCE",
                interface_type="UART",
                health_state=HealthState.ONLINE,
                confidence=1.1,
                payload={},
                receipt_id="receipt-invalid",
                source_clock=SourceClock.DEVICE,
                stale_after_ms=1000,
                calibration_version="1",
            )

    def test_health_event_preserves_transition_and_diagnostics(self):
        event = HealthEvent(
            event_id="health-1",
            event_type=HealthEventType.DEGRADED,
            module_id="mic-roof-left",
            node_id="audio-node",
            owning_handmaiden="Velvet",
            timestamp=123.0,
            severity=HealthSeverity.WARNING,
            state_before=HealthState.ONLINE,
            state_after=HealthState.DEGRADED,
            confidence=0.8,
            diagnostic_payload={"noise_floor_shift_db": 6.0},
            receipt_id="receipt-health-1",
            recovery_action="recalibrate noise floor",
            fallback_owner="Velvet",
        )

        record = event.to_event_protocol()
        self.assertEqual(record["event_type"], "HEALTH_DEGRADED")
        self.assertEqual(record["payload"]["state_after"], "DEGRADED")

    def test_node_manifest_rejects_capability_overlap(self):
        with self.assertRaises(ValueError):
            NodeCapabilityManifest(
                node_id="node-1",
                display_name="Node One",
                hardware_model="test",
                operating_system="linux",
                compute_limits={},
                memory_limits={},
                storage_limits={},
                allowed_capabilities=("vehicle.write",),
                forbidden_capabilities=("vehicle.write",),
                owning_handmaiden="Velvet",
            )

    def test_node_manifest_permission_is_explicit(self):
        manifest = NodeCapabilityManifest(
            node_id="velour-node",
            display_name="Velour Librarian",
            hardware_model="Luckfox Lyra Ultra",
            operating_system="Linux",
            compute_limits={"cores": 3},
            memory_limits={"ram_mb": 512},
            storage_limits={"emmc_gb": 8},
            network_interfaces=("ethernet",),
            attached_sensors=(),
            controlled_outputs=(),
            allowed_capabilities=("receipts.append", "archive.index"),
            forbidden_capabilities=("vehicle.control",),
            owning_handmaiden="Velour",
            fallback_owner="Velvet",
            receipt_types=("NODE_HEALTH", "ARCHIVE_WRITE"),
        )
        self.assertTrue(manifest.permits("receipts.append"))
        self.assertFalse(manifest.permits("vehicle.control"))

    def test_lifecycle_allows_only_declared_transitions(self):
        lifecycle = standard_lifecycle_contract("jade-climate", "Jade")
        self.assertTrue(
            lifecycle.can_transition(
                ModuleLifecycleState.READY,
                ModuleLifecycleState.ACTIVE,
            )
        )
        self.assertFalse(
            lifecycle.can_transition(
                ModuleLifecycleState.DISCOVERED,
                ModuleLifecycleState.ACTIVE,
            )
        )
        self.assertFalse(
            lifecycle.policy(ModuleLifecycleState.DEGRADED).authority_allowed
        )
        with self.assertRaises(ValueError):
            lifecycle.require_transition(
                ModuleLifecycleState.DISCOVERED,
                ModuleLifecycleState.ACTIVE,
            )

    def test_capability_ownership_marks_forbidden_callers(self):
        ownership = CapabilityOwnership(
            capability_name="medical.minimal_risk_stop",
            owning_handmaiden="Temperance",
            inputs=("driver_presence", "seizure_evidence"),
            outputs=("minimal_risk_stop_proposal",),
            dependencies=("runtime", "court", "charlotte"),
            fallback_owner="Velvet",
            authority_level=CapabilityAuthority.GOVERNED_EMERGENCY,
            receipt_types=("MEDICAL_ASSESSMENT",),
            degraded_behavior="notify and retain observation only",
            forbidden_direct_callers=("ui", "language_model"),
        )
        self.assertTrue(ownership.caller_is_forbidden("ui"))
        self.assertFalse(ownership.caller_is_forbidden("runtime"))

    def test_control_interface_requires_command_contract(self):
        with self.assertRaises(ValueError):
            VehicleInterfaceContract(
                interface_id="brake",
                purpose="brake actuator",
                vehicle_targets=("Dakota",),
                authority_mode=VehicleInterfaceAuthority.GOVERNED_CONTROL,
                owning_handmaiden="Charlotte",
                physical_interface="relay",
                data_format="feedback-json",
                update_frequency_hz=50.0,
                command_format=None,
                receipt_type="BRAKE_ACTUATION",
                safe_failure_behavior="release and fail closed",
                adapter_boundary="vehicle.brake.v1",
                simulation_adapter_available=True,
                allowed_surfaces=("bench",),
            )

    def test_vehicle_interface_allowlist_is_surface_specific(self):
        contract = VehicleInterfaceContract(
            interface_id="can-observer",
            purpose="read-only CAN observation",
            vehicle_targets=("Tiburon", "Western Star", "Dakota"),
            authority_mode=VehicleInterfaceAuthority.READ_ONLY,
            owning_handmaiden="Ruby",
            physical_interface="CAN",
            data_format="decoded-signals-v1",
            update_frequency_hz=100.0,
            command_format=None,
            receipt_type="CAN_OBSERVATION",
            safe_failure_behavior="stop publishing and emit STALE",
            adapter_boundary="vehicle.can.observe.v1",
            simulation_adapter_available=True,
            allowed_surfaces=("Tiburon", "Western Star", "Dakota", "bench"),
        )
        self.assertTrue(contract.allowed_on("Western Star"))
        self.assertFalse(contract.allowed_on("house"))


if __name__ == "__main__":
    unittest.main()
