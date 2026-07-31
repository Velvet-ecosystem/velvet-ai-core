"""Tests for Module Lab promotion gates."""

import unittest

from velvet.core.module_promotion import ModulePromotionEvidence, PromotionGate


class ModulePromotionTests(unittest.TestCase):
    def test_all_gates_and_receipts_are_required(self):
        with self.assertRaises(ValueError):
            ModulePromotionEvidence(
                module_id="seat-monitor",
                gate_results={},
                evidence_receipts={},
            )

    def test_failed_gate_blocks_human_review_readiness(self):
        results = {gate: True for gate in PromotionGate}
        results[PromotionGate.AUTHORITY_BYPASS] = False
        receipts = {gate: "receipt-%s" % gate.value for gate in PromotionGate}
        evidence = ModulePromotionEvidence(
            module_id="seat-monitor",
            gate_results=results,
            evidence_receipts=receipts,
            fuzz_targets=("seat-json",),
        )
        self.assertFalse(evidence.ready_for_human_promotion_review)
        with self.assertRaises(ValueError):
            evidence.assert_ready_for_human_promotion_review()

    def test_passed_gates_only_offer_human_review(self):
        results = {gate: True for gate in PromotionGate}
        receipts = {gate: "receipt-%s" % gate.value for gate in PromotionGate}
        evidence = ModulePromotionEvidence(
            module_id="gnss",
            gate_results=results,
            evidence_receipts=receipts,
            fuzz_targets=("nmea",),
        )
        self.assertTrue(evidence.ready_for_human_promotion_review)


if __name__ == "__main__":
    unittest.main()
