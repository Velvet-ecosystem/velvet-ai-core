from velvet.core.recognition_adapters import (
    AdapterContext,
    AdapterHealth,
    AdapterReading,
    CameraRecognitionAdapter,
    NfcRecognitionAdapter,
)
from velvet.core.recognition_device_registry import (
    DeviceBindingState,
    DeviceTransport,
    RecognitionDeviceBinding,
    RecognitionDeviceRegistry,
)
from velvet.core.recognition_runtime_handoff import (
    HandoffHealth,
    RecognitionRuntimeHandoff,
)


class CameraStub(CameraRecognitionAdapter):
    def __init__(self, module_id, node_id, failed=False):
        super().__init__(module_id, node_id)
        self.failed = failed

    def read(self, context):
        return AdapterReading(
            confidence=0.91,
            receipt_id="receipt.camera",
            details={"match": "candidate"},
            raw_reference="file://frame.jpg",
            health=AdapterHealth.FAILED if self.failed else AdapterHealth.ONLINE,
        )


class NfcStub(NfcRecognitionAdapter):
    def read(self, context):
        return AdapterReading(
            confidence=1.0,
            receipt_id="receipt.nfc",
            trusted_credential=True,
            simulated=False,
        )


def binding(kind="camera", state=DeviceBindingState.ACTIVE):
    return RecognitionDeviceBinding(
        binding_id="binding.%s" % kind,
        device_id="device.%s" % kind,
        module_id="module.%s" % kind,
        node_id="node.main",
        adapter_kind=kind,
        transport=DeviceTransport.USB,
        endpoint="/dev/%s0" % kind,
        owning_handmaiden="native-brain",
        approved_by="runtime",
        approval_receipt_id="receipt.approval.%s" % kind,
        state=state,
    )


def registry_with(*bindings):
    registry = RecognitionDeviceRegistry()
    for item in bindings:
        registry.register(item)
    return registry


def test_collects_only_from_active_explicit_binding():
    item = binding()
    registry = registry_with(item)
    handoff = RecognitionRuntimeHandoff(
        registry,
        lambda approved: CameraStub(approved.module_id, approved.node_id),
    )

    assert handoff.bind_active() == ()
    result = handoff.collect(
        {
            item.binding_id: AdapterContext(
                candidate_entity_id="entity.mister",
                observed_at=10.0,
                frame_id="cabin",
                location_id="driver-zone",
                body_position="driver-seat",
            )
        }
    )

    assert len(result.observations) == 1
    assert result.observations[0].source_module_id == item.module_id
    assert result.health_events[0].health == HandoffHealth.OBSERVATION_ACCEPTED
    assert result.authority_granted is False
    assert result.execution_performed is False


def test_inactive_binding_never_collects():
    item = binding(state=DeviceBindingState.SUSPENDED)
    handoff = RecognitionRuntimeHandoff(
        registry_with(item),
        lambda approved: CameraStub(approved.module_id, approved.node_id),
    )

    result = handoff.collect(
        {item.binding_id: AdapterContext("entity.mister", 5.0)}
    )

    assert result.observations == ()
    assert result.health_events[0].health == HandoffHealth.BINDING_INACTIVE


def test_missing_runtime_adapter_emits_health_failure():
    item = binding()
    handoff = RecognitionRuntimeHandoff(registry_with(item), lambda approved: None)

    bind_events = handoff.bind_active()
    assert bind_events[0].health == HandoffHealth.ADAPTER_UNAVAILABLE

    result = handoff.collect(
        {item.binding_id: AdapterContext("entity.mister", 5.0)}
    )
    assert result.observations == ()
    assert result.health_events[0].health == HandoffHealth.ADAPTER_UNAVAILABLE


def test_failed_hardware_never_enters_recognition_spine():
    item = binding()
    handoff = RecognitionRuntimeHandoff(
        registry_with(item),
        lambda approved: CameraStub(approved.module_id, approved.node_id, failed=True),
    )
    handoff.bind_active()

    result = handoff.collect(
        {item.binding_id: AdapterContext("entity.mister", 5.0)}
    )

    assert result.observations == ()
    assert result.health_events[0].health == HandoffHealth.ADAPTER_FAILED


def test_adapter_identity_must_match_binding():
    item = binding()
    handoff = RecognitionRuntimeHandoff(
        registry_with(item),
        lambda approved: CameraStub("wrong.module", approved.node_id),
    )

    events = handoff.bind_active()
    assert events[0].health == HandoffHealth.ADAPTER_UNAVAILABLE
    assert "does not match approved binding" in events[0].reason


def test_adapter_modality_must_match_binding():
    item = binding()
    handoff = RecognitionRuntimeHandoff(
        registry_with(item),
        lambda approved: NfcStub(approved.module_id, approved.node_id),
    )

    events = handoff.bind_active()
    assert events[0].health == HandoffHealth.ADAPTER_UNAVAILABLE
    assert "modality" in events[0].reason


def test_unbind_removes_runtime_adapter():
    item = binding()
    handoff = RecognitionRuntimeHandoff(
        registry_with(item),
        lambda approved: CameraStub(approved.module_id, approved.node_id),
    )
    handoff.bind_active()
    handoff.unbind(item.binding_id)

    result = handoff.collect(
        {item.binding_id: AdapterContext("entity.mister", 5.0)}
    )
    assert result.observations == ()
    assert result.health_events[0].health == HandoffHealth.ADAPTER_UNAVAILABLE


def test_discovery_is_forbidden():
    handoff = RecognitionRuntimeHandoff(RecognitionDeviceRegistry(), lambda binding: None)
    try:
        handoff.discover()
    except RuntimeError as exc:
        assert "cannot discover" in str(exc)
    else:
        raise AssertionError("discovery must be forbidden")
