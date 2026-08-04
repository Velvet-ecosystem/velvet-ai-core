from __future__ import annotations

import unittest
from dataclasses import replace

from velvet.core.recognition_adapters import (
    AdapterContext,
    AdapterHealth,
    AdapterReading,
    CameraRecognitionAdapter,
    NfcRecognitionAdapter,
    SeatPresenceRecognitionAdapter,
    VoiceRecognitionAdapter,
)
from velvet.core.recognition_evidence import RecognitionModality


class FakeCamera(CameraRecognitionAdapter):
    def read(self, context: AdapterContext) -> AdapterReading:
        return AdapterReading(
            confidence=0.91,
            receipt_id="receipt-camera",
            details={"detector": "face-v1"},
            raw_reference="file://frame.jpg",
        )


class FakeVoice(VoiceRecognitionAdapter):
    def read(self, context: AdapterContext) -> AdapterReading:
        return AdapterReading(
            confidence=0.84,
            receipt_id="receipt-voice",
            details={"speaker_model": "speaker-v1"},
            health=AdapterHealth.DEGRADED,
        )


class FakeNfc(NfcRecognitionAdapter):
    def __init__(self, simulated: bool) -> None:
        super().__init__("nfc.owner-token", "node-cabin")
        self._simulated = simulated

    def read(self, context: AdapterContext) -> AdapterReading:
        return AdapterReading(
            confidence=1.0,
            receipt_id="receipt-nfc",
            trusted_credential=True,
            simulated=self._simulated,
            details={"credential_class": "owner-token"},
        )


class FakeSeat(SeatPresenceRecognitionAdapter):
    def read(self, context: AdapterContext) -> AdapterReading:
        return AdapterReading(
            confidence=0.96,
            receipt_id="receipt-seat",
            details={"occupied": True},
        )


class FailedCamera(CameraRecognitionAdapter):
    def read(self, context: AdapterContext) -> AdapterReading:
        return AdapterReading(
            confidence=0.0,
            receipt_id="receipt-failed",
            health=AdapterHealth.FAILED,
        )


def recognition_context() -> AdapterContext:
    return AdapterContext(
        candidate_entity_id="person.mister",
        observed_at=100.0,
        frame_id="vehicle-cabin",
        location_id="driver-zone",
        body_position="driver-seat",
    )


class RecognitionAdapterTests(unittest.TestCase):
    def test_camera_adapter_normalizes_hardware_reading(self) -> None:
        observation = FakeCamera("camera.cabin", "node-vision").observe(
            recognition_context()
        )
        self.assertEqual(observation.modality, RecognitionModality.IMAGE)
        self.assertEqual(observation.candidate_entity_id, "person.mister")
        self.assertEqual(observation.source_module_id, "camera.cabin")
        self.assertEqual(observation.source_node_id, "node-vision")
        self.assertEqual(observation.confidence, 0.91)
        self.assertEqual(observation.details["adapter_health"], "ONLINE")
        self.assertFalse(observation.authority_granted)
        self.assertFalse(observation.execution_performed)

    def test_degraded_voice_reading_remains_usable_and_visible(self) -> None:
        observation = FakeVoice("microphone.cabin", "node-audio").observe(
            recognition_context()
        )
        self.assertEqual(observation.modality, RecognitionModality.VOICE)
        self.assertEqual(observation.details["adapter_health"], "DEGRADED")
        self.assertEqual(observation.confidence, 0.84)

    def test_simulated_trusted_nfc_remains_simulated(self) -> None:
        observation = FakeNfc(simulated=True).observe(recognition_context())
        self.assertTrue(observation.trusted_credential)
        self.assertTrue(observation.simulated)
        self.assertEqual(observation.modality, RecognitionModality.NFC)

    def test_real_trusted_nfc_remains_distinct_from_simulated(self) -> None:
        observation = FakeNfc(simulated=False).observe(recognition_context())
        self.assertTrue(observation.trusted_credential)
        self.assertFalse(observation.simulated)

    def test_seat_adapter_preserves_body_position(self) -> None:
        observation = FakeSeat("seat.driver", "node-seat").observe(
            recognition_context()
        )
        self.assertEqual(observation.modality, RecognitionModality.BEHAVIOR)
        self.assertEqual(observation.body_position, "driver-seat")
        self.assertEqual(observation.location_id, "driver-zone")

    def test_failed_adapter_does_not_emit_recognition_evidence(self) -> None:
        adapter = FailedCamera("camera.failed", "node-vision")
        with self.assertRaisesRegex(RuntimeError, "adapter reading failed"):
            adapter.observe(recognition_context())

    def test_invalid_adapter_context_and_readings_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            AdapterContext(candidate_entity_id="", observed_at=1.0)
        with self.assertRaises(ValueError):
            AdapterReading(confidence=1.5, receipt_id="receipt")
        with self.assertRaises(ValueError):
            AdapterReading(confidence=0.5, receipt_id="")

    def test_observation_cannot_be_rewritten_to_claim_authority(self) -> None:
        observation = FakeCamera("camera.cabin", "node-vision").observe(
            recognition_context()
        )
        with self.assertRaisesRegex(
            ValueError, "cannot claim authority or execution"
        ):
            replace(observation, authority_granted=True)


if __name__ == "__main__":
    unittest.main()
