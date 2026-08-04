"""Tests for multimodal recognition evidence and correlation boundaries."""

import unittest

from velvet.core.recognition_evidence import (
    RecognitionDisposition,
    RecognitionEvidenceFusion,
    RecognitionModality,
    RecognitionObservation,
)


class RecognitionEvidenceTests(unittest.TestCase):
    def observation(
        self,
        observation_id,
        modality,
        confidence,
        candidate="person-mister",
        observed_at=100.0,
        source=None,
        trusted=False,
        simulated=False,
        location="tiburon.driver-seat",
        frame="tiburon-cabin",
        position="driver",
    ):
        return RecognitionObservation(
            observation_id=observation_id,
            candidate_entity_id=candidate,
            modality=modality,
            source_module_id=source or ("sensor-" + observation_id),
            source_node_id="up2-founder",
            observed_at=observed_at,
            confidence=confidence,
            receipt_id="receipt-" + observation_id,
            frame_id=frame,
            location_id=location,
            body_position=position,
            trusted_credential=trusted,
            simulated=simulated,
            details={"bounded_match": True},
        )

    def test_single_face_match_is_possible_not_verified(self):
        fusion = RecognitionEvidenceFusion().fuse(
            "person-mister",
            (
                self.observation(
                    "face-1", RecognitionModality.IMAGE, 0.88
                ),
            ),
        )
        self.assertEqual(fusion.disposition, RecognitionDisposition.POSSIBLE)
        self.assertFalse(fusion.authority_granted)
        self.assertFalse(fusion.execution_performed)

    def test_face_and_voice_can_be_likely(self):
        fusion = RecognitionEvidenceFusion().fuse(
            "person-mister",
            (
                self.observation("face", RecognitionModality.IMAGE, 0.82),
                self.observation("voice", RecognitionModality.VOICE, 0.78),
            ),
        )
        self.assertEqual(fusion.disposition, RecognitionDisposition.LIKELY)
        self.assertEqual(fusion.modality_count, 2)

    def test_three_modalities_and_real_credential_are_corroborated(self):
        fusion = RecognitionEvidenceFusion().fuse(
            "person-mister",
            (
                self.observation("face", RecognitionModality.IMAGE, 0.88),
                self.observation("voice", RecognitionModality.VOICE, 0.84),
                self.observation(
                    "nfc",
                    RecognitionModality.NFC,
                    0.99,
                    trusted=True,
                ),
            ),
        )
        self.assertEqual(
            fusion.disposition,
            RecognitionDisposition.CORROBORATED,
        )
        self.assertEqual(len(fusion.identity_evidence), 3)

    def test_simulated_credential_cannot_complete_corroboration(self):
        fusion = RecognitionEvidenceFusion().fuse(
            "person-mister",
            (
                self.observation("face", RecognitionModality.IMAGE, 0.90),
                self.observation("voice", RecognitionModality.VOICE, 0.90),
                self.observation(
                    "nfc",
                    RecognitionModality.NFC,
                    0.99,
                    trusted=True,
                    simulated=True,
                ),
            ),
        )
        self.assertEqual(fusion.disposition, RecognitionDisposition.LIKELY)

    def test_different_locations_are_disputed(self):
        fusion = RecognitionEvidenceFusion().fuse(
            "person-mister",
            (
                self.observation("face", RecognitionModality.IMAGE, 0.9),
                self.observation(
                    "voice",
                    RecognitionModality.VOICE,
                    0.9,
                    location="house.kitchen",
                    frame="house",
                    position="standing",
                ),
            ),
        )
        self.assertEqual(fusion.disposition, RecognitionDisposition.DISPUTED)

    def test_observations_outside_time_window_do_not_correlate(self):
        fusion = RecognitionEvidenceFusion().fuse(
            "person-mister",
            (
                self.observation(
                    "face", RecognitionModality.IMAGE, 0.9, observed_at=100.0
                ),
                self.observation(
                    "voice", RecognitionModality.VOICE, 0.9, observed_at=106.0
                ),
            ),
        )
        self.assertEqual(
            fusion.disposition,
            RecognitionDisposition.INSUFFICIENT,
        )

    def test_competing_candidate_with_similar_support_is_disputed(self):
        fusion = RecognitionEvidenceFusion().fuse(
            "person-mister",
            (
                self.observation("face", RecognitionModality.IMAGE, 0.78),
                self.observation("voice", RecognitionModality.VOICE, 0.76),
                self.observation(
                    "other-face",
                    RecognitionModality.IMAGE,
                    0.72,
                    candidate="person-unknown-2",
                ),
            ),
        )
        self.assertEqual(fusion.disposition, RecognitionDisposition.DISPUTED)
        self.assertEqual(
            fusion.conflicting_candidate_ids,
            ("person-unknown-2",),
        )

    def test_recognition_converts_to_identity_evidence_without_authority(self):
        observation = self.observation(
            "nfc", RecognitionModality.NFC, 0.99, trusted=True
        )
        evidence = observation.to_identity_evidence()
        self.assertEqual(evidence.evidence_type, "recognition.nfc")
        self.assertEqual(
            evidence.details["candidate_entity_id"],
            "person-mister",
        )
        self.assertNotIn("authority_granted", evidence.details)

    def test_observation_rejects_authority_claim(self):
        with self.assertRaises(ValueError):
            RecognitionObservation(
                observation_id="bad",
                candidate_entity_id="person-mister",
                modality=RecognitionModality.IMAGE,
                source_module_id="camera",
                source_node_id="up2",
                observed_at=1.0,
                confidence=0.9,
                receipt_id="receipt-bad",
                authority_granted=True,
            )


if __name__ == "__main__":
    unittest.main()
