import unittest

from ai_brain.native_brain.recognition_bench import (
    RecognitionBenchPipeline,
    SimulatedRecognitionAdapters,
    SimulatedRecognitionScenario,
)
from ai_brain.native_brain.world_context import ContextFactDisposition
from velvet.core.recognition_evidence import RecognitionDisposition
from velvet.core.schemas.world_model import EntityIdentity, IdentityStatus
from velvet.core.world_event_bridge import WorldEventType


class RecognitionBenchTests(unittest.TestCase):
    def _identity(self):
        return EntityIdentity(
            entity_id="person.mister",
            entity_type="person",
            canonical_name="Mister",
            status=IdentityStatus.UNKNOWN,
            confidence=0.0,
        )

    def test_adapters_emit_four_bounded_modalities(self):
        scenario = SimulatedRecognitionScenario(
            candidate_entity_id="person.mister",
            observed_at=100.0,
        )
        observations = SimulatedRecognitionAdapters.collect(scenario)

        self.assertEqual(len(observations), 4)
        self.assertTrue(all(item.simulated for item in observations))
        self.assertTrue(all(not item.authority_granted for item in observations))
        self.assertTrue(all(not item.execution_performed for item in observations))
        self.assertEqual(
            {item.body_position for item in observations},
            {"driver-seat"},
        )

    def test_simulated_nfc_cannot_complete_corroboration(self):
        result = RecognitionBenchPipeline().run(
            self._identity(),
            SimulatedRecognitionScenario(
                candidate_entity_id="person.mister",
                observed_at=100.0,
                observations_simulated=True,
            ),
        )

        self.assertEqual(result.fusion.disposition, RecognitionDisposition.LIKELY)
        self.assertNotEqual(
            result.fusion.disposition,
            RecognitionDisposition.CORROBORATED,
        )
        self.assertEqual(
            result.recognition_event.event_type,
            WorldEventType.RECOGNITION_EVIDENCE_FUSED,
        )
        self.assertEqual(result.recognition_fact.disposition, ContextFactDisposition.CURRENT)
        self.assertFalse(result.authority_granted)
        self.assertFalse(result.execution_performed)

    def test_hardware_equivalent_mode_can_reach_corroborated(self):
        result = RecognitionBenchPipeline().run(
            self._identity(),
            SimulatedRecognitionScenario(
                candidate_entity_id="person.mister",
                observed_at=100.0,
                observations_simulated=False,
            ),
        )

        self.assertEqual(
            result.fusion.disposition,
            RecognitionDisposition.CORROBORATED,
        )
        self.assertGreaterEqual(result.fusion.modality_count, 3)
        self.assertTrue(
            any(
                item.trusted_credential and not item.simulated
                for item in result.observations
            )
        )

    def test_conflicting_seat_position_becomes_disputed_context(self):
        result = RecognitionBenchPipeline().run(
            self._identity(),
            SimulatedRecognitionScenario(
                candidate_entity_id="person.mister",
                observed_at=100.0,
                conflicting_seat_position=True,
            ),
        )

        self.assertEqual(
            result.fusion.disposition,
            RecognitionDisposition.DISPUTED,
        )
        self.assertEqual(
            result.recognition_event.event_type,
            WorldEventType.RECOGNITION_EVIDENCE_DISPUTED,
        )
        self.assertEqual(
            result.recognition_fact.disposition,
            ContextFactDisposition.DISPUTED,
        )

    def test_camera_only_remains_possible(self):
        result = RecognitionBenchPipeline().run(
            self._identity(),
            SimulatedRecognitionScenario(
                candidate_entity_id="person.mister",
                observed_at=100.0,
                include_voice=False,
                include_nfc=False,
                include_seat=False,
            ),
        )

        self.assertEqual(result.fusion.disposition, RecognitionDisposition.POSSIBLE)
        self.assertEqual(result.fusion.modality_count, 1)

    def test_identity_and_candidate_must_match(self):
        with self.assertRaises(ValueError):
            RecognitionBenchPipeline().run(
                self._identity(),
                SimulatedRecognitionScenario(
                    candidate_entity_id="person.someone-else",
                    observed_at=100.0,
                ),
            )

    def test_context_ages_without_becoming_authority(self):
        pipeline = RecognitionBenchPipeline()
        pipeline.run(
            self._identity(),
            SimulatedRecognitionScenario(
                candidate_entity_id="person.mister",
                observed_at=100.0,
            ),
        )

        context = pipeline.context_snapshot(now=200.0)
        facts = context.facts_for("person.mister")
        self.assertTrue(facts)
        self.assertTrue(
            all(
                fact.disposition in (
                    ContextFactDisposition.STALE,
                    ContextFactDisposition.DISPUTED,
                    ContextFactDisposition.REJECTED,
                )
                for fact in facts
            )
        )
        self.assertFalse(context.authority_granted)
        self.assertFalse(context.execution_performed)


if __name__ == "__main__":
    unittest.main()
