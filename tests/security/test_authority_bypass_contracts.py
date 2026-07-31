"""Authority-bypass contract tests below UI and model layers."""

import unittest
from datetime import datetime, timezone

from ai_brain.native_brain import (
    BodyPracticeSkeleton,
    EventProtocolAdapter,
    EventProtocolError,
    FakeOrganAdapter,
    FaultProfile,
    NativeBrain,
    OrganContract,
)
from velvet.core.module_lifecycle import (
    ModuleLifecycleState,
    standard_lifecycle_contract,
)
from velvet.core.schemas import (
    CapabilityAuthority,
    CapabilityOwnership,
    VehicleInterfaceAuthority,
    VehicleInterfaceContract,
)


class AuthorityBypassContractTests(unittest.TestCase):
    def test_ui_approval_field_cannot_create_executor_authority(self):
        adapter = EventProtocolAdapter()
        with self.assertRaises(EventProtocolError):
            adapter.normalize(
                {
                    "event_type": "ui.approval.observed",
                    "source": "interface",
                    "payload": {
                        "approved": True,
                        "executor_name": "brake-actuator",
                    },
                }
            )

    def test_simulation_cannot_smuggle_capability_token(self):
        contract = OrganContract(
            organ_name="Ruby",
            event_type="vehicle.signal.observed",
            source="fake-can",
        )
        fake = FakeOrganAdapter(
            contract=contract,
            reader=lambda: {"speed_kph": 0},
            faults=FaultProfile(
                impossible_values={"capability_token": "fake-token"}
            ),
            clock=lambda: datetime(2026, 7, 31, tzinfo=timezone.utc),
        )

        with self.assertRaises(EventProtocolError):
            BodyPracticeSkeleton(NativeBrain()).run(fake)

    def test_bench_interface_is_not_vehicle_permission(self):
        interface = VehicleInterfaceContract(
            interface_id="bench-relay",
            purpose="bench actuator feedback",
            vehicle_targets=("bench",),
            authority_mode=VehicleInterfaceAuthority.BENCH_ONLY,
            owning_handmaiden="Charlotte",
            physical_interface="GPIO",
            data_format="state-v1",
            update_frequency_hz=10,
            command_format=None,
            receipt_type="BENCH_RELAY",
            safe_failure_behavior="de-energize",
            adapter_boundary="bench.relay.v1",
            simulation_adapter_available=True,
            allowed_surfaces=("bench",),
        )
        self.assertFalse(interface.allowed_on("Tiburon"))
        self.assertFalse(interface.allowed_on("Dakota"))

    def test_ready_lifecycle_does_not_allow_authority(self):
        lifecycle = standard_lifecycle_contract("brake", "Charlotte")
        self.assertFalse(
            lifecycle.policy(ModuleLifecycleState.READY).authority_allowed
        )
        self.assertTrue(
            lifecycle.policy(ModuleLifecycleState.ACTIVE).authority_allowed
        )

    def test_forbidden_direct_caller_remains_explicit(self):
        ownership = CapabilityOwnership(
            capability_name="vehicle.brake",
            owning_handmaiden="Charlotte",
            inputs=("governed_intent",),
            outputs=("brake_executor_request",),
            dependencies=("runtime", "court", "safety_gate"),
            fallback_owner=None,
            authority_level=CapabilityAuthority.GOVERNED_CONTROL,
            receipt_types=("BRAKE_REQUEST",),
            degraded_behavior="refuse and emit health receipt",
            forbidden_direct_callers=("ui", "language_model", "simulation"),
        )
        self.assertTrue(ownership.caller_is_forbidden("ui"))
        self.assertTrue(ownership.caller_is_forbidden("simulation"))


if __name__ == "__main__":
    unittest.main()
