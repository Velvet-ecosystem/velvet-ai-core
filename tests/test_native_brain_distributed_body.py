# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain.distributed_body import (
    CandidateMode,
    DegradationMode,
    DistributedBodyPlanner,
    NodeAdvertisement,
    NodeAvailability,
    NodeTier,
    PlacementDisposition,
    WorkRequirement,
)


class DistributedBodyPlannerTests(unittest.TestCase):
    def node(
        self,
        node_id,
        organ,
        tier,
        capabilities,
        load=0.2,
        health=0.9,
        availability=NodeAvailability.AVAILABLE,
        **kwargs,
    ):
        return NodeAdvertisement(
            node_id=node_id,
            organ=organ,
            tier=tier,
            capabilities=tuple(capabilities),
            current_load=load,
            health=health,
            availability=availability,
            **kwargs,
        )

    def work(self, **kwargs):
        values = {
            "work_id": "work.audio.filter.1",
            "work_class": "audio.filtering",
            "required_capabilities": ("audio.filter",),
        }
        values.update(kwargs)
        return WorkRequirement(**values)

    def test_narrow_specialist_is_preferred_over_queen(self):
        specialist = self.node(
            "nova-audio",
            "audio",
            NodeTier.SPECIALIST_LINUX,
            ("audio.filter",),
            accepted_work_classes=("audio.filtering",),
        )
        queen = self.node(
            "founder",
            "queen",
            NodeTier.QUEEN,
            ("audio.filter", "whole.system.reason"),
            load=0.1,
        )

        result = DistributedBodyPlanner().propose(self.work(), (queen, specialist))

        self.assertEqual(result.candidates[0].node_id, "nova-audio")
        self.assertIs(result.candidates[0].mode, CandidateMode.PRIMARY)
        self.assertEqual(result.authority, "none")
        self.assertTrue(result.requires_runtime_placement)

    def test_queen_is_required_for_whole_system_coordination(self):
        specialist = self.node(
            "lyra-runtime",
            "runtime",
            NodeTier.SPECIALIST_LINUX,
            ("whole.system.reason",),
        )
        queen = self.node(
            "founder",
            "queen",
            NodeTier.QUEEN,
            ("whole.system.reason",),
        )
        requirement = self.work(
            work_id="work.system.plan.1",
            work_class="whole.system.planning",
            required_capabilities=("whole.system.reason",),
            whole_system_coordination=True,
        )

        result = DistributedBodyPlanner().propose(requirement, (specialist, queen))

        self.assertEqual(tuple(item.node_id for item in result.candidates), ("founder",))
        self.assertIn("queen-whole-system-role", result.candidates[0].reasons)

    def test_overloaded_primary_is_skipped_for_compatible_overflow_node(self):
        primary = self.node(
            "nova-audio",
            "audio",
            NodeTier.SPECIALIST_LINUX,
            ("audio.filter",),
            load=0.95,
            accepted_work_classes=("audio.filtering",),
        )
        overflow = self.node(
            "lyra-security",
            "security",
            NodeTier.SPECIALIST_LINUX,
            (),
            fallback_capabilities=("audio.filter",),
            overflow_capable=True,
        )

        result = DistributedBodyPlanner().propose(self.work(), (primary, overflow))

        self.assertEqual(result.candidates[0].node_id, "lyra-security")
        self.assertIs(result.candidates[0].mode, CandidateMode.OVERFLOW)
        self.assertIs(result.degradation, DegradationMode.FULL_REPLACEMENT)
        self.assertTrue(any("load-or-task-limit-exceeded" in reason for reason in result.reasons))

    def test_node_may_temporarily_absorb_compatible_duty(self):
        substitute = self.node(
            "heavy-local",
            "heavy-cognition",
            NodeTier.HEAVY_LINUX,
            ("local.reason",),
            temporary_absorption_capabilities=("audio.filter",),
        )

        result = DistributedBodyPlanner().propose(self.work(), (substitute,))

        self.assertIs(result.candidates[0].mode, CandidateMode.TEMPORARY_ABSORPTION)
        self.assertIs(result.degradation, DegradationMode.FULL_REPLACEMENT)

    def test_node_can_refuse_work_outside_its_limits(self):
        node = self.node(
            "lyra-security",
            "security",
            NodeTier.SPECIALIST_LINUX,
            ("audio.filter",),
            refused_work_classes=("audio.filtering",),
        )

        result = DistributedBodyPlanner().propose(self.work(), (node,))

        self.assertIs(result.disposition, PlacementDisposition.UNAVAILABLE)
        self.assertTrue(any("work-class-refused" in reason for reason in result.reasons))

    def test_partial_replacement_reports_degradation(self):
        node = self.node(
            "small-sensor-node",
            "sensor-fusion",
            NodeTier.SPECIALIST_LINUX,
            ("sensor.filter",),
        )
        requirement = self.work(
            required_capabilities=("sensor.filter", "local.pattern"),
            allow_partial=True,
            partial_result_useful=True,
        )

        result = DistributedBodyPlanner().propose(requirement, (node,))

        self.assertIs(result.disposition, PlacementDisposition.DEGRADED_CANDIDATE)
        self.assertIs(result.degradation, DegradationMode.PARTIAL_REPLACEMENT)
        self.assertEqual(result.candidates[0].missing_capabilities, ("local.pattern",))

    def test_observe_only_fallback_is_explicit(self):
        node = self.node(
            "can-observer",
            "vehicle-observer",
            NodeTier.SPECIALIST_LINUX,
            ("can.observe",),
        )
        requirement = self.work(
            work_class="vehicle.control",
            required_capabilities=("can.control",),
            observe_only_capability="can.observe",
        )

        result = DistributedBodyPlanner().propose(requirement, (node,))

        self.assertIs(result.disposition, PlacementDisposition.DEGRADED_CANDIDATE)
        self.assertIs(result.degradation, DegradationMode.OBSERVE_ONLY)
        self.assertIs(result.candidates[0].mode, CandidateMode.OBSERVE_ONLY)

    def test_failed_node_does_not_take_down_unrelated_body_capabilities(self):
        failed_audio = self.node(
            "nova-audio",
            "audio",
            NodeTier.SPECIALIST_LINUX,
            ("audio.filter",),
            availability=NodeAvailability.OFFLINE,
        )
        healthy_security = self.node(
            "lyra-security",
            "security",
            NodeTier.SPECIALIST_LINUX,
            ("security.watch",),
        )

        result = DistributedBodyPlanner().propose(self.work(), (failed_audio, healthy_security))

        self.assertIs(result.disposition, PlacementDisposition.UNAVAILABLE)
        self.assertIs(result.degradation, DegradationMode.CAPABILITY_UNAVAILABLE)
        self.assertTrue(any("nova-audio:availability:offline" == reason for reason in result.reasons))

    def test_unverified_nodes_are_not_candidates(self):
        node = self.node(
            "unknown-node",
            "unknown",
            NodeTier.HEAVY_LINUX,
            ("audio.filter",),
            body_verified=False,
        )

        result = DistributedBodyPlanner().propose(self.work(), (node,))

        self.assertFalse(result.candidates)
        self.assertTrue(any("body-not-verified" in reason for reason in result.reasons))

    def test_consequential_work_keeps_court_requirement(self):
        node = self.node(
            "runtime-node",
            "runtime",
            NodeTier.SPECIALIST_LINUX,
            ("relay.prepare",),
        )
        requirement = self.work(
            work_id="work.relay.prepare.1",
            work_class="relay.preparation",
            required_capabilities=("relay.prepare",),
            consequential=True,
        )

        result = DistributedBodyPlanner().propose(requirement, (node,))

        self.assertTrue(result.requires_court_authorization)
        self.assertEqual(result.authority, "none")
        self.assertTrue(result.escalate_results_to_queen)

    def test_identical_inputs_produce_identical_proposals(self):
        nodes = (
            self.node(
                "sensor-a",
                "sensor-fusion",
                NodeTier.SPECIALIST_LINUX,
                ("audio.filter",),
            ),
            self.node(
                "sensor-b",
                "sensor-fusion-backup",
                NodeTier.SPECIALIST_LINUX,
                ("audio.filter",),
                load=0.4,
            ),
        )
        planner = DistributedBodyPlanner()

        first = planner.propose(self.work(), nodes)
        second = planner.propose(self.work(), nodes)

        self.assertEqual(first, second)
        self.assertEqual(first.authority, "none")


if __name__ == "__main__":
    unittest.main()
