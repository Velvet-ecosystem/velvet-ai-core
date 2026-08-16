# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.cognition.event_workspace import (
    CurrentEventWorkspace,
    WorkspaceObservation,
)
from velvet.core.cognition.learning_session import (
    LearningCandidateKind,
    LearningEligibility,
    LearningSessionBudget,
    LearningSessionState,
    LearningSessionSupervisor,
)


def workspace_snapshot(body_id="body-1", simulated=True):
    workspace = CurrentEventWorkspace(
        body_id=body_id,
        node_id="node-1",
        id_factory=lambda prefix: "%s-fixed" % prefix,
        replay_state="fixture" if simulated else "live",
    )
    observation = WorkspaceObservation(
        event_id="obs-1",
        event_type="vehicle.fake.coolant.observed" if simulated else "vehicle.coolant.observed",
        source="ghost-can-fixture" if simulated else "ruby.sensor",
        body_id=body_id,
        observed_at=1.0,
        monotonic_time=1.0,
        confidence=0.8,
        payload={"celsius": 92.0},
        source_refs=("source-1",),
        stale_after_ms=10000,
        simulated=simulated,
    )
    workspace.open(
        event_kind="coolant-review",
        observation=observation,
        now=1.0,
        cognitive_event_id="cog-1",
    )
    return workspace.snapshot()


class LearningSessionTests(unittest.TestCase):
    def supervisor(self, budget=None):
        supervisor = LearningSessionSupervisor(
            body_id="body-1",
            node_id="queen-1",
            budget=budget,
        )
        supervisor.propose(
            objective="review coolant evidence",
            evidence_refs=("seed-1",),
            session_id="learning-1",
        )
        return supervisor

    def test_session_completes_without_granting_authority(self):
        supervisor = self.supervisor()
        supervisor.evaluate_eligibility(
            LearningEligibility(
                allowed=True,
                reason="quiet powered study window",
                source_refs=("eligibility-1",),
            )
        )
        snapshot = workspace_snapshot(simulated=True)
        supervisor.attach_workspace(
            snapshot,
            simulated_observation_refs=("obs-1",),
        )
        candidate = supervisor.add_candidate(
            kind=LearningCandidateKind.EXPLANATION,
            summary="coolant observation is suitable for later comparison",
            evidence_refs=("obs-1",),
            confidence=0.6,
            candidate_id="candidate-1",
        )
        supervisor.request_review("bounded study is ready for review")
        supervisor.complete("review completed without applying changes")

        result = supervisor.snapshot()
        self.assertEqual(result.state, LearningSessionState.COMPLETED)
        self.assertIn("obs-1", result.simulated_evidence_refs)
        self.assertIn("eligibility-1", result.eligibility_refs)
        self.assertFalse(result.canonical)
        self.assertFalse(result.memory_write_authorized)
        self.assertFalse(result.runtime_placement_authorized)
        self.assertFalse(result.court_authorized)
        self.assertFalse(result.execution_authorized)
        self.assertFalse(result.actuation_authorized)
        self.assertEqual(result.authority, "none")
        self.assertFalse(candidate.canonical)
        self.assertFalse(candidate.changes_applied)
        self.assertEqual(candidate.authority, "none")

    def test_ineligible_session_pauses_and_can_be_rechecked(self):
        supervisor = self.supervisor()
        supervisor.evaluate_eligibility(
            LearningEligibility(
                allowed=False,
                reason="owner interaction has priority",
            )
        )
        self.assertEqual(supervisor.state, LearningSessionState.PAUSED)

        supervisor.evaluate_eligibility(
            LearningEligibility(
                allowed=True,
                reason="owner interaction ended and study is permitted",
            )
        )
        self.assertEqual(supervisor.state, LearningSessionState.OPEN)
        self.assertEqual(supervisor.snapshot().pause_reason, "")

    def test_workspace_from_another_body_is_rejected(self):
        supervisor = self.supervisor()
        supervisor.evaluate_eligibility(
            LearningEligibility(True, "study permitted")
        )

        with self.assertRaises(ValueError):
            supervisor.attach_workspace(
                workspace_snapshot(body_id="other-body"),
                simulated_observation_refs=("obs-1",),
            )

        self.assertEqual(supervisor.state, LearningSessionState.OPEN)
        self.assertEqual(supervisor.snapshot().workspace_refs, ())

    def test_simulated_provenance_must_belong_to_the_workspace(self):
        supervisor = self.supervisor()
        supervisor.evaluate_eligibility(
            LearningEligibility(True, "study permitted")
        )

        with self.assertRaises(ValueError):
            supervisor.attach_workspace(
                workspace_snapshot(simulated=True),
                simulated_observation_refs=("not-in-workspace",),
            )

        self.assertEqual(supervisor.snapshot().simulated_evidence_refs, ())

    def test_candidate_requires_evidence_already_in_session(self):
        supervisor = self.supervisor()
        supervisor.evaluate_eligibility(
            LearningEligibility(True, "study permitted")
        )
        supervisor.attach_workspace(
            workspace_snapshot(simulated=False),
            simulated_observation_refs=(),
        )

        with self.assertRaises(ValueError):
            supervisor.add_candidate(
                kind=LearningCandidateKind.EXPLANATION,
                summary="unsupported conclusion",
                evidence_refs=("unknown-evidence",),
                confidence=0.5,
            )

        self.assertEqual(supervisor.candidates(), ())

    def test_step_budget_fails_closed_before_candidate_mutation(self):
        supervisor = self.supervisor(
            LearningSessionBudget(
                max_steps=2,
                max_workspace_refs=2,
                max_candidates=2,
                max_distributed_work_refs=2,
            )
        )
        supervisor.evaluate_eligibility(
            LearningEligibility(True, "study permitted")
        )
        supervisor.attach_workspace(
            workspace_snapshot(simulated=False),
            simulated_observation_refs=(),
        )
        before = supervisor.snapshot()

        with self.assertRaises(RuntimeError):
            supervisor.add_candidate(
                kind=LearningCandidateKind.NO_CHANGE,
                summary="no change justified",
                evidence_refs=("obs-1",),
                confidence=0.8,
                candidate_id="candidate-should-not-exist",
            )

        after = supervisor.snapshot()
        self.assertEqual(before.steps_used, 2)
        self.assertEqual(after.steps_used, 2)
        self.assertEqual(after.candidate_ids, ())
        self.assertEqual(supervisor.candidates(), ())
        self.assertEqual(supervisor.state, LearningSessionState.STUDYING)


if __name__ == "__main__":
    unittest.main()
