import pytest

from velvet.core.native_brain.body_snapshot_conversation import BodySnapshotConversationResolver
from velvet.core.native_brain.conversation_ingress import (
    ConversationMeaningKind,
    ConversationWorkRequest,
    GroundedConversationMeaning,
)
from velvet.core.native_brain.conversation_resolver_chain import ConversationResolverChain
from velvet.core.native_brain.library_evidence_conversation import (
    LIBRARY_EVIDENCE_SCHEMA,
    LibraryEvidenceConversationResolver,
    validate_library_evidence,
)


def request(text="What torque should the pulley bolt use?", **overrides):
    values = {
        "conversation_id": "bench",
        "turn_id": "bench:1",
        "turn_number": 1,
        "text": text,
        "modality": "text",
        "audience": "owner",
        "act": "question",
        "strategy": "answer",
        "requires_authority_check": False,
        "may_speak": True,
    }
    values.update(overrides)
    return ConversationWorkRequest(**values)


def evidence_document(**overrides):
    result = {
        "item_id": "item_manual",
        "chunk_id": "chk_123",
        "title": "Tiburon Workshop Manual",
        "source": "manufacturer",
        "trust_class": "primary",
        "sha256": "a" * 64,
        "score": 3.0,
        "snippet": "Tighten the pulley bolt to 170 N·m after seating the pulley.",
        "retrieval_method": "full_text_deterministic",
        "lifecycle_state": "active",
        "warnings": [],
    }
    result.update(overrides.pop("result", {}))
    document = {
        "schema": LIBRARY_EVIDENCE_SCHEMA,
        "query": "What torque should the pulley bolt use?",
        "read_only": True,
        "reference_only": True,
        "authority": "none",
        "results": [result],
    }
    document.update(overrides)
    return document


def test_library_question_returns_reference_only_evidence():
    resolver = LibraryEvidenceConversationResolver(lambda query, limit: evidence_document())

    meaning = resolver(request())

    assert meaning.response_kind is ConversationMeaningKind.EVIDENCE
    assert meaning.fact_id == "library.evidence"
    assert meaning.source_label == "Tiburon Workshop Manual"
    assert "170 N·m" in meaning.value
    assert "reference-only" in meaning.qualifiers
    assert meaning.source_refs == (
        "library:item:item_manual",
        "library:sha256:" + "a" * 64,
        "library:chunk:chk_123",
    )
    assert meaning.grants_authority is False


def test_contiguous_window_preserves_every_touched_chunk_ref():
    resolver = LibraryEvidenceConversationResolver(
        lambda query, limit: evidence_document(
            result={
                "chunk_ids": ["chk_123", "chk_124", "chk_125"],
                "windowed": True,
                "window_truncated": False,
                "snippet": (
                    "## Core principles - Local first. - Provenance before confidence. "
                    "- Preserve the source. - Trust is graded. - Retrieval is not belief. "
                    "- Receipts matter. - Knowledge is modular. - Models are optional. "
                    "- Currency is metadata, not truth."
                ),
            }
        )
    )

    meaning = resolver(request("What are Velour Library's core principles?"))

    assert meaning.response_kind is ConversationMeaningKind.EVIDENCE
    assert "Currency is metadata, not truth" in meaning.value
    assert "evidence-window:contiguous" in meaning.qualifiers
    assert "evidence-window:truncated" not in meaning.qualifiers
    assert meaning.source_refs == (
        "library:item:item_manual",
        "library:sha256:" + "a" * 64,
        "library:chunk:chk_123",
        "library:chunk:chk_124",
        "library:chunk:chk_125",
    )


def test_truncated_window_is_disclosed_and_window_shape_is_bounded():
    resolver = LibraryEvidenceConversationResolver(
        lambda query, limit: evidence_document(
            result={
                "chunk_ids": ["chk_123", "chk_124"],
                "windowed": True,
                "window_truncated": True,
            }
        )
    )
    meaning = resolver(request())
    assert "evidence-window:truncated" in meaning.qualifiers

    with pytest.raises(ValueError, match="chunk_ids exceed"):
        validate_library_evidence(
            evidence_document(
                result={
                    "chunk_ids": ["chk_123", "chk_124", "chk_125", "chk_126"],
                    "windowed": True,
                }
            )
        )

    with pytest.raises(ValueError, match="seed chunk"):
        validate_library_evidence(
            evidence_document(
                result={"chunk_ids": ["chk_other"], "windowed": True}
            )
        )

    with pytest.raises(ValueError, match="must be windowed"):
        validate_library_evidence(
            evidence_document(result={"window_truncated": True})
        )


def test_retrieval_score_is_not_copied_into_truth_confidence():
    resolver = LibraryEvidenceConversationResolver(
        lambda query, limit: evidence_document(result={"score": 999999.0})
    )

    meaning = resolver(request())

    assert meaning.confidence == 1.0
    assert "retrieval:full_text_deterministic" in meaning.qualifiers


def test_metadata_only_hit_is_not_repeated_as_an_answer():
    resolver = LibraryEvidenceConversationResolver(
        lambda query, limit: evidence_document(
            result={"chunk_id": None, "retrieval_method": "metadata"}
        )
    )

    meaning = resolver(request())

    assert meaning.response_kind is ConversationMeaningKind.UNAVAILABLE
    assert "library-no-passage" in meaning.qualifiers


def test_library_does_not_handle_actions_or_non_questions():
    calls = []

    def provider(query, limit):
        calls.append(query)
        return evidence_document()

    resolver = LibraryEvidenceConversationResolver(provider)

    action = resolver(
        request(
            "Open the window",
            act="command_like",
            requires_authority_check=True,
        )
    )
    observation = resolver(request("The engine sounds rough", act="observation"))

    assert action.response_kind is ConversationMeaningKind.AUTHORITY_REQUIRED
    assert observation.response_kind is ConversationMeaningKind.UNAVAILABLE
    assert calls == []


def test_library_evidence_contract_rejects_authority_and_unbounded_results():
    with pytest.raises(ValueError, match="cannot carry authority"):
        validate_library_evidence(evidence_document(authority="runtime"))

    with pytest.raises(ValueError, match="result count"):
        validate_library_evidence(
            evidence_document(results=[evidence_document()["results"][0]] * 21)
        )


def test_stale_source_is_preserved_as_a_warning_not_hidden():
    resolver = LibraryEvidenceConversationResolver(
        lambda query, limit: evidence_document(
            result={"warnings": ["source_stale", "freshness_deadline_passed"]}
        )
    )

    meaning = resolver(request())

    assert "source-stale" in meaning.qualifiers


def test_resolver_chain_prefers_body_then_falls_through_to_library():
    body_calls = []
    library_calls = []

    def body(request):
        body_calls.append(request.text)
        if "cabin" in request.text.casefold():
            return GroundedConversationMeaning(
                response_kind=ConversationMeaningKind.FACT,
                fact_id="cabin.temperature",
                value=21.5,
                unit="C",
                confidence=0.99,
            )
        return GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.UNAVAILABLE,
            confidence=0.0,
            qualifiers=("unsupported-body-fact",),
        )

    def library(request):
        library_calls.append(request.text)
        return GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.EVIDENCE,
            confidence=1.0,
            fact_id="library.evidence",
            value="Manual passage",
            source_label="Workshop Manual",
            qualifiers=("reference-only",),
            source_refs=("library:item:item1",),
        )

    chain = ConversationResolverChain((body, library))

    body_answer = chain(request("What is the cabin temperature?"))
    library_answer = chain(request("What torque should the bolt use?"))

    assert body_answer.response_kind is ConversationMeaningKind.FACT
    assert library_answer.response_kind is ConversationMeaningKind.EVIDENCE
    assert library_calls == ["What torque should the bolt use?"]
