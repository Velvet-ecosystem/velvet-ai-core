import pytest

from velvet.core.recognition_adapters import (
    CameraRecognitionAdapter,
    NfcRecognitionAdapter,
    SeatPresenceRecognitionAdapter,
    VoiceRecognitionAdapter,
)
from velvet.core.recognition_device_registry import (
    DeviceBindingState,
    DeviceTransport,
    RecognitionDeviceBinding,
    RecognitionDeviceRegistry,
)
from velvet.core.recognition_evidence import RecognitionModality


def binding(
    binding_id="bind.camera",
    device_id="usb.camera.1",
    module_id="camera.cabin.front",
    adapter_kind="camera",
    state=DeviceBindingState.DECLARED,
    simulated=False,
):
    return RecognitionDeviceBinding(
        binding_id=binding_id,
        device_id=device_id,
        module_id=module_id,
        node_id="founder-up2",
        adapter_kind=adapter_kind,
        transport=DeviceTransport.USB,
        endpoint="/dev/video0",
        owning_handmaiden="Velvet",
        approved_by="runtime",
        approval_receipt_id="receipt.binding.1",
        state=state,
        configuration={"frame_id": "vehicle-cabin"},
        simulated=simulated,
    )


def test_declared_binding_requires_explicit_activation_before_adapter_creation():
    item = binding()

    with pytest.raises(RuntimeError, match="only active bindings"):
        item.create_adapter()

    active = item.with_state(DeviceBindingState.ACTIVE, "receipt.activate.1")
    adapter = active.create_adapter()

    assert isinstance(adapter, CameraRecognitionAdapter)
    assert adapter.module_id == "camera.cabin.front"
    assert active.authority_granted is False
    assert active.execution_performed is False


def test_registry_registers_only_explicit_bindings_and_preserves_history():
    registry = RecognitionDeviceRegistry()

    change = registry.register(binding())
    registry.activate("bind.camera", "receipt.activate.1")

    assert change.previous_state is None
    assert registry.get("bind.camera").state == DeviceBindingState.ACTIVE
    assert registry.by_device("usb.camera.1").binding_id == "bind.camera"
    assert len(registry.history()) == 2
    assert all(not item.authority_granted for item in registry.history())


def test_registry_rejects_duplicate_device_module_and_binding_ids():
    registry = RecognitionDeviceRegistry()
    registry.register(binding())

    with pytest.raises(ValueError, match="binding_id"):
        registry.register(binding(device_id="usb.camera.2", module_id="camera.2"))

    with pytest.raises(ValueError, match="device_id"):
        registry.register(
            binding(
                binding_id="bind.voice",
                module_id="voice.cabin",
                adapter_kind="voice",
            )
        )

    with pytest.raises(ValueError, match="module_id"):
        registry.register(
            binding(
                binding_id="bind.voice",
                device_id="usb.microphone.1",
                adapter_kind="voice",
            )
        )


def test_storage_scanning_and_device_self_registration_are_forbidden():
    registry = RecognitionDeviceRegistry()

    with pytest.raises(RuntimeError, match="scanning are forbidden"):
        registry.discover("/dev")

    with pytest.raises(RuntimeError, match="cannot self-register"):
        registry.self_register({"device_id": "surprise"})


def test_active_registry_builds_correct_adapter_types_without_device_choice():
    registry = RecognitionDeviceRegistry()
    definitions = (
        binding(),
        binding(
            binding_id="bind.voice",
            device_id="usb.microphone.1",
            module_id="voice.cabin.center",
            adapter_kind="voice",
        ),
        binding(
            binding_id="bind.nfc",
            device_id="uart.nfc.1",
            module_id="nfc.owner.presence",
            adapter_kind="nfc",
        ),
        binding(
            binding_id="bind.seat",
            device_id="uart.seat.1",
            module_id="seat.driver.presence",
            adapter_kind="seat_presence",
        ),
    )
    for item in definitions:
        registry.register(item)
        registry.activate(item.binding_id, "receipt.activate.%s" % item.binding_id)

    adapters = registry.active_adapters()

    assert any(isinstance(item, CameraRecognitionAdapter) for item in adapters)
    assert any(isinstance(item, VoiceRecognitionAdapter) for item in adapters)
    assert any(isinstance(item, NfcRecognitionAdapter) for item in adapters)
    assert any(isinstance(item, SeatPresenceRecognitionAdapter) for item in adapters)


def test_modality_filter_returns_only_active_matching_bindings():
    registry = RecognitionDeviceRegistry()
    camera = binding()
    voice = binding(
        binding_id="bind.voice",
        device_id="usb.microphone.1",
        module_id="voice.cabin.center",
        adapter_kind="voice",
    )
    registry.register(camera)
    registry.register(voice)
    registry.activate(camera.binding_id, "receipt.activate.camera")

    active_cameras = registry.active_bindings(RecognitionModality.IMAGE)
    active_voices = registry.active_bindings(RecognitionModality.VOICE)

    assert active_cameras == (registry.get(camera.binding_id),)
    assert active_voices == ()


def test_suspended_binding_disappears_from_active_adapter_set():
    registry = RecognitionDeviceRegistry()
    registry.register(binding())
    registry.activate("bind.camera", "receipt.activate.1")
    assert len(registry.active_adapters()) == 1

    registry.suspend("bind.camera", "receipt.suspend.1")

    assert registry.active_adapters() == ()
    assert registry.get("bind.camera").state == DeviceBindingState.SUSPENDED


def test_retired_binding_cannot_be_reactivated():
    registry = RecognitionDeviceRegistry()
    registry.register(binding())
    registry.retire("bind.camera", "receipt.retire.1")

    with pytest.raises(ValueError, match="cannot be reactivated"):
        registry.activate("bind.camera", "receipt.activate.again")


def test_simulated_binding_remains_explicitly_marked():
    item = binding(simulated=True)

    assert item.simulated is True
    assert item.configuration["frame_id"] == "vehicle-cabin"


def test_binding_rejects_unknown_adapter_and_authority_claims():
    with pytest.raises(ValueError, match="unsupported adapter_kind"):
        binding(adapter_kind="mystery")

    with pytest.raises(ValueError, match="cannot claim authority"):
        RecognitionDeviceBinding(
            binding_id="bind.bad",
            device_id="device.bad",
            module_id="module.bad",
            node_id="node.bad",
            adapter_kind="camera",
            transport=DeviceTransport.USB,
            endpoint="/dev/video9",
            owning_handmaiden="Velvet",
            approved_by="runtime",
            approval_receipt_id="receipt.bad",
            authority_granted=True,
        )
