"""Tests for bounded evidence freshness and confidence decay."""

import unittest
from datetime import datetime, timedelta, timezone

from ai_brain.native_brain import (
    EvidenceContribution,
    EvidenceFreshnessEvaluator,
    EvidenceFusionEngine,
    FreshnessDisposition,
    FusionDisposition,
    NativeBrain,
)


class EvidenceFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 30, 20, 0, tzinfo=timezone.utc)
        self.evaluator = EvidenceFreshnessEvaluator(
            fresh_for_seconds=10.0,
            stale_after_seconds=110.0,
        )

    def test_fresh_evidence_retains_confidence(self) -> None:
        contribution = EvidenceContribution(
            "Temperance",
            "driver_unresponsive",
            0.8,
            observed_at=self.now - timedelta(seconds=5),
        )

        freshness = self.evaluator.evaluate(contribution, self.now)

        self.assertEqual(freshness.disposition, FreshnessDisposition.FRESH)
        self.assertEqual(freshness.effective_confidence, 0.8)
        self.assertFalse(freshness.authority_granted)
        self.assertFalse(freshness.execution_performed)

    def test_aging_evidence_decays_confidence(self) -> None:
        contribution = EvidenceContribution(
            "Camera",
            "driver_unresponsive",
            0.8,
            observed_at=self.now - timedelta(seconds=60),
        )

        freshness = self.evaluator.evaluate(contribution, self.now)

        self.assertEqual(freshness.disposition, FreshnessDisposition.AGING)
        self.assertEqual(freshness.effective_confidence, 0.4)

    def test_stale_evidence_has_no_effective_confidence(self) -> None:
        contribution = EvidenceContribution(
            "SeatMonitor",
            "occupied",
            0.9,
            observed_at=self.now - timedelta(seconds=111),
        )

        freshness = self.evaluator.evaluate(contribution, self.now)

        self.assertEqual(freshness.disposition, FreshnessDisposition.STALE)
        self.assertEqual(freshness.effective_confidence, 0.0)

    def test_future_timestamp_is_invalid(self) -> None:
        contribution = EvidenceContribution(
            "Nova",
            "glass_break",
            0.7,
            observed_at=self.now + timedelta(seconds=1),
        )

        freshness = self.evaluator.evaluate(contribution, self.now)

        self.assertEqual(freshness.disposition, FreshnessDisposition.INVALID)
        self.assertEqual(freshness.effective_confidence, 0.0)

    def test_fusion_excludes_stale_evidence(self) -> None:
        contributions = (
            EvidenceContribution(
                "Temperance",
                "driver_unresponsive",
                0.9,
                observed_at=self.now - timedelta(seconds=5),
            ),
            EvidenceContribution(
                "Charlotte",
                "driver_unresponsive",
                0.9,
                observed_at=self.now - timedelta(seconds=111),
            ),
        )
        fusion = EvidenceFusionEngine(freshness=self.evaluator).fuse(
            "driver state",
            contributions,
            self.now,
        )

        self.assertEqual(
            fusion.disposition,
            FusionDisposition.INSUFFICIENT_EVIDENCE,
        )
        self.assertEqual(
            fusion.stale_contribution_ids,
            (contributions[1].contribution_id,),
        )
        self.assertEqual(
            fusion.active_contribution_ids,
            (contributions[0].contribution_id,),
        )

    def test_fusion_uses_effective_not_base_confidence(self) -> None:
        contributions = (
            EvidenceContribution(
                "Temperance",
                "driver_unresponsive",
                0.8,
                observed_at=self.now - timedelta(seconds=60),
            ),
            EvidenceContribution(
                "Charlotte",
                "driver_unresponsive",
                0.6,
                observed_at=self.now - timedelta(seconds=60),
            ),
        )
        fusion = EvidenceFusionEngine(freshness=self.evaluator).fuse(
            "driver state",
            contributions,
            self.now,
        )

        self.assertEqual(fusion.disposition, FusionDisposition.COHERENT)
        self.assertEqual(fusion.confidence, 0.35)
        self.assertFalse(fusion.authority_granted)
        self.assertFalse(fusion.execution_performed)

    def test_native_brain_exposes_append_only_freshness_reviews(self) -> None:
        contribution = EvidenceContribution(
            "Ruby",
            "engine_running",
            0.95,
            observed_at=self.now,
        )

        reviews = NativeBrain().evaluate_evidence_freshness(
            (contribution,),
            self.now,
        )

        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].contribution_id, contribution.contribution_id)
        self.assertEqual(contribution.confidence, 0.95)


if __name__ == "__main__":
    unittest.main()
