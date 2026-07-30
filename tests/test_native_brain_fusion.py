"""Tests for non-authoritative cross-organ evidence fusion."""

import unittest

from ai_brain.native_brain import (
    EvidenceContribution,
    EvidenceFusionEngine,
    FusionDisposition,
    NativeBrain,
)


class EvidenceFusionTests(unittest.TestCase):
    def test_coherent_distinct_organs_are_fused(self) -> None:
        contributions = (
            EvidenceContribution("Temperance", "driver_unresponsive", 0.8),
            EvidenceContribution("Charlotte", "driver_unresponsive", 0.9),
        )
        fusion = NativeBrain().fuse_evidence("driver state", contributions)
        self.assertEqual(fusion.disposition, FusionDisposition.COHERENT)
        self.assertFalse(fusion.authority_granted)
        self.assertFalse(fusion.execution_performed)

    def test_conflicting_claims_are_preserved(self) -> None:
        fusion = EvidenceFusionEngine().fuse(
            "seat state",
            (
                EvidenceContribution("SeatMonitor", "occupied", 0.9),
                EvidenceContribution("Camera", "empty", 0.7),
            ),
        )
        self.assertEqual(fusion.disposition, FusionDisposition.CONFLICTED)
        self.assertIn("conflicting", fusion.rationale)

    def test_one_organ_is_insufficient(self) -> None:
        fusion = EvidenceFusionEngine().fuse(
            "cabin sound",
            (EvidenceContribution("Nova", "glass_break", 0.8),),
        )
        self.assertEqual(
            fusion.disposition, FusionDisposition.INSUFFICIENT_EVIDENCE
        )

    def test_empty_subject_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceFusionEngine().fuse(" ", ())


if __name__ == "__main__":
    unittest.main()
