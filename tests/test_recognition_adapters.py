from __future__ import annotations

from dataclasses import replace

import pytest

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


def context() -> AdapterContext:
    return AdapterContext(
        candidate_entity_id="person.mister",
        observed_at=100.0,
        frame_id="vehicle-cabin",
        location_id="driver-zone",
        body_position="driver-seat",
    )


def test_camera_adapter_normalizes_hardware_reading() -> None:
    observation = FakeCamera("camera.cabin", "node-vision").observe(context())

    assert observation.modality == RecognitionModality.IMAGE
    assert observation.candidate_entity_id == "person.mister"
    assert observation.source_module_id == "camera.cabin"
    assert observation.source_node_id == "node-vision"
    assert observation.confidence == 0.91
    assert observation.details["adapter_health"] == "ONLINE"
    assert observation.authority_granted is False
    assert observation.execution_performed is False


def test_degraded_voice_reading_remains_usable_and_visible() -> None:
    observation = FakeVoice("microphone.cabin", "node-audio").observe(context())

    assert observation.modality == RecognitionModality.VOICE
    assert observation.details["adapter_health"] == "DEGRADED"
    assert observation.confidence == 0.84


def test_simulated_trusted_nfc_remains_simulated() -> None:
    observation = FakeNfc(simulated=True).observe(context())

    assert observation.trusted_credential is True
    assert observation.simulated is True
    assert observation.modality == RecognitionModality.NFC


def test_real_trusted_nfc_remains_distinct_from_simulated() -> None:
    observation = FakeNfc(simulated=False).observe(context())

    assert observation.trusted_credential is True
    assert observation.simulated is False


def test_seat_adapter_preserves_body_position() -> None:
    observation = FakeSeat("seat.driver", "node-seat").observe(context())

    assert observation.modality == RecognitionModality.BEHAVIOR
    assert observation.body_position == "driver-seat"
    assert observation.location_id == "driver-zone"


def test_failed_adapter_does_not_emit_recognition_evidence() -> None:
    adapter = FailedCamera("camera.failed", "node-vision")

    with pytest.raises(RuntimeError, match="adapter reading failed"):
        adapter.observe(context())


def test_invalid_adapter_context_and_readings_are_rejected() -> None:
    with pytest.raises(ValueError):
        AdapterContext(candidate_entity_id="", observed_at=1.0)
    with pytest.raises(ValueError):
        AdapterReading(confidence=1.5, receipt_id="receipt")
    with pytest.raises(ValueError):
        AdapterReading(confidence=0.5, receipt_id="")


def test_observation_cannot_be_rewritten_to_claim_authority() -> None:
    observation = FakeCamera("camera.cabin", "node-vision").observe(context())

    with pytest.raises(ValueError, match="cannot claim authority or execution"):
        replace(observation, authority_granted=True)
