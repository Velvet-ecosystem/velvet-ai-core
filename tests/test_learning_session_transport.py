# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.cognition.learning_session import (
    LearningEligibility,
    LearningSessionSnapshot,
    LearningSessionState,
    LearningSessionSupervisor,
    LearningSessionTransition,
)
from velvet.core.cognition.learning_session_transport import (
    project_learning_session_transition,
)


class LearningSessionTransportTests(unittest.TestCase):
    def test_projection_keeps_objective_and_reason_prose_local(self):
        supervisor = LearningSessionSupervisor(body_id="founder", node_id="velvet-founder")
        transition = supervisor.propose(
            objective="Study the recurring coolant observation and compare local manuals.",
            evidence_refs=("evidence-001",),
            session_id="learning-session-001",
        )
        snapshot = supervisor.snapshot()

        projection = project_learning_session_transition(
            snapshot,
            transition,
            subject_ref="study-subject-001",
        )
        payload = projection.to_record_kwargs()

        self.assertEqual(projection.event_type, "learning.session.proposed")
        self.assertEqual(payload["subject_ref"], "study-subject-001")
        self.assertEqual(payload["reason_code"], "session_proposed")
        self.assertNotIn("objective", payload)
        self.assertNotIn("reason", payload)
        self.assertNotIn("Study the recurring coolant", repr(payload))

    def test_projection_preserves_simulated_vehicle_evidence_refs(self):
        snapshot = LearningSessionSnapshot(
            session_id="learning-session-002",
            body_id="founder",
            node_id="velvet-founder",
            objective="Compare fake-car observation against bounded expectations.",
            state=LearningSessionState.STUDYING,
            evidence_refs=("ghost-can-001", "manual-001"),
            simulated_evidence_refs=("ghost-can-001",),
            eligibility_refs=("eligibility-001",),
            workspace_refs=("cog-001",),
            distributed_work_refs=(),
            candidate_ids=(),
            degraded_reasons=(),
            pause_reason="",
            completion_reason="",
            steps_used=2,
        )
        transition = LearningSessionTransition(
            session_id="learning-session-002",
            previous_state=LearningSessionState.OPEN,
            state=LearningSessionState.STUDYING,
            reason="bounded cognitive workspace associated",
            step=2,
        )

        projection = project_learning_session_transition(
            snapshot,
            transition,
            subject_ref="study-subject-ghost-001",
        )

        self.assertEqual(projection.simulated_evidence_refs, ("ghost-can-001",))
        self.assertEqual(projection.evidence_refs, ("ghost-can-001", "manual-001"))
        self.assertEqual(projection.reason_code, "study_progress")

    def test_projection_rejects_cross_session_mix(self):
        supervisor = LearningSessionSupervisor(body_id="founder", node_id="velvet-founder")
        transition = supervisor.propose(
            objective="Study one bounded issue.",
            evidence_refs=("evidence-001",),
            session_id="learning-session-003",
        )
        snapshot = supervisor.snapshot()
        wrong_transition = LearningSessionTransition(
            session_id="learning-session-other",
            previous_state=transition.previous_state,
            state=transition.state,
            reason=transition.reason,
            step=transition.step,
        )

        with self.assertRaisesRegex(ValueError, "different sessions"):
            project_learning_session_transition(
                snapshot,
                wrong_transition,
                subject_ref="study-subject-003",
            )

    def test_recorded_eligibility_transition_can_project_after_open(self):
        supervisor = LearningSessionSupervisor(body_id="founder", node_id="velvet-founder")
        supervisor.propose(
            objective="Study one bounded issue.",
            evidence_refs=("evidence-001",),
            session_id="learning-session-004",
        )
        supervisor.evaluate_eligibility(
            LearningEligibility(
                allowed=True,
                reason="quiet maintenance window approved",
                source_refs=("eligibility-001",),
            )
        )
        snapshot = supervisor.snapshot()
        transitions = supervisor.transitions()
        eligibility_transition = transitions[1]

        self.assertEqual(snapshot.state, LearningSessionState.OPEN)
        self.assertEqual(
            eligibility_transition.state,
            LearningSessionState.ELIGIBILITY_CHECK,
        )

        projection = project_learning_session_transition(
            snapshot,
            eligibility_transition,
            subject_ref="study-subject-004",
        )

        self.assertEqual(
            projection.event_type,
            "learning.session.eligibility_checked",
        )
        self.assertEqual(projection.state, "ELIGIBILITY_CHECK")
        self.assertEqual(projection.steps_used, eligibility_transition.step)
        self.assertIn("eligibility-001", projection.eligibility_refs)

    def test_projection_rejects_future_step(self):
        supervisor = LearningSessionSupervisor(body_id="founder", node_id="velvet-founder")
        transition = supervisor.propose(
            objective="Study one bounded issue.",
            evidence_refs=("evidence-001",),
            session_id="learning-session-005",
        )
        snapshot = supervisor.snapshot()
        future = LearningSessionTransition(
            session_id=transition.session_id,
            previous_state=LearningSessionState.PROPOSED,
            state=LearningSessionState.PAUSED,
            reason="priority work",
            step=snapshot.steps_used + 1,
        )

        with self.assertRaisesRegex(ValueError, "step"):
            project_learning_session_transition(
                snapshot,
                future,
                subject_ref="study-subject-005",
            )


if __name__ == "__main__":
    unittest.main()
