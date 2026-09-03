import pytest

from velvet.core.native_brain.conversation_ingress import (
    CORE_CONVERSATION_MEANING_EVENT,
    ConversationMeaningKind,
    GroundedConversationMeaning,
    conversation_work_request_from_event,
    handle_conversation_turn,
)


def turn_event(**overrides):
    event = {
        "event": "velvet.language.conversation.turn",
        "schema_version": "0.1",
        "conversation_id": "bench-chat",
        "turn_id": "bench-chat:1",
        "turn_number": 1,
        "text": "What is the cabin temperature?",
        "modality": "text",
        "audience": "owner",
        "act": "question",
        "strategy": "answer",
        "requires_authority_check": False,
        "may_speak": True,
        "authority_granted": False,
    }
    event.update(overrides)
    return event


def test_language_turn_becomes_read_only_core_observation():
    request = conversation_work_request_from_event(turn_event())
    observation = request.to_observation()

    assert request.conversation_id == "bench-chat"
    assert request.authority_granted is False
    assert observation.event_type == "velvet.language.conversation.turn"
    assert observation.source == "velvet-language"
    assert observation.read_only is True
    assert observation.payload["authority_granted"] is False


def test_grounded_resolver_returns_structured_meaning_not_human_wording():
    def resolver(request):
        assert request.act == "question"
        return GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.FACT,
            fact_id="cabin.temperature",
            value=21.5,
            unit="C",
            confidence=0.99,
            qualifiers=("fresh",),
            source_refs=("body-state:cabin-temp",),
        )

    result = handle_conversation_turn(turn_event(), resolver=resolver)

    assert result["event"] == CORE_CONVERSATION_MEANING_EVENT
    assert result["response_kind"] == "fact"
    assert result["fact_id"] == "cabin.temperature"
    assert result["value"] == 21.5
    assert result["unit"] == "C"
    assert result["source_refs"] == ["body-state:cabin-temp"]
    assert result["authority"] == "none"
    assert result["grants_authority"] is False
    assert "text" not in result


def test_missing_resolver_fails_truthfully_to_unavailable_meaning():
    result = handle_conversation_turn(turn_event())

    assert result["response_kind"] == "unavailable"
    assert result["value"] is None
    assert "no-grounded-resolver" in result["qualifiers"]
    assert result["grants_execution"] is False


def test_action_like_turn_preserves_authority_check_without_granting_it():
    result = handle_conversation_turn(
        turn_event(
            text="Open the window",
            act="command_like",
            strategy="request_authority_check",
            requires_authority_check=True,
        )
    )

    assert result["requires_authority_check"] is True
    assert result["authority"] == "none"
    assert result["grants_authority"] is False
    assert result["grants_actuation"] is False


def test_ingress_rejects_authority_claims_and_bad_contracts():
    with pytest.raises(ValueError, match="authority_granted=false"):
        conversation_work_request_from_event(turn_event(authority_granted=True))

    with pytest.raises(ValueError, match="unexpected conversation event type"):
        conversation_work_request_from_event(turn_event(event="something.else"))

    with pytest.raises(ValueError, match="unsupported conversation schema"):
        conversation_work_request_from_event(turn_event(schema_version="99"))


def test_grounded_meaning_cannot_smuggle_authority_or_structured_values():
    with pytest.raises(ValueError, match="cannot carry authority"):
        GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.UNAVAILABLE,
            confidence=0.0,
            authority="runtime",
        )

    with pytest.raises(ValueError, match="must be a scalar"):
        GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.FACT,
            fact_id="bad.fact",
            value={"hidden": "structure"},
            confidence=1.0,
        )


def test_resolver_must_return_grounded_meaning_contract():
    def bad_resolver(_request):
        return {"response_kind": "fact"}

    with pytest.raises(TypeError, match="GroundedConversationMeaning"):
        handle_conversation_turn(turn_event(), resolver=bad_resolver)
