from velvet.core.native_brain.conversation_ingress import (
    ConversationMeaningKind,
    ConversationWorkRequest,
)
from velvet.core.native_brain.library_evidence_conversation import (
    LIBRARY_EVIDENCE_SCHEMA,
    LibraryEvidenceConversationResolver,
)


def request(text="What torque should the pulley bolt use?"):
    return ConversationWorkRequest(
        conversation_id="bench",
        turn_id="bench:1",
        turn_number=1,
        text=text,
        modality="text",
        audience="owner",
        act="question",
        strategy="answer",
        requires_authority_check=False,
        may_speak=True,
    )


def result(item_id, title, snippet, *, sha_char, warnings=()):
    return {
        "item_id": item_id,
        "chunk_id": "chk_" + item_id,
        "title": title,
        "source": "manual",
        "trust_class": "primary",
        "sha256": sha_char * 64,
        "score": 5.0,
        "snippet": snippet,
        "retrieval_method": "full_text_deterministic",
        "lifecycle_state": "active",
        "warnings": list(warnings),
    }


def document(*results):
    return {
        "schema": LIBRARY_EVIDENCE_SCHEMA,
        "query": "test",
        "read_only": True,
        "reference_only": True,
        "authority": "none",
        "results": list(results),
    }


def test_equivalent_torque_units_are_corroborated_after_normalization():
    evidence = document(
        result(
            "manual_a",
            "Factory Manual",
            "Tighten the crank pulley bolt to 170 N·m after seating the pulley.",
            sha_char="a",
        ),
        result(
            "manual_b",
            "Service Reference",
            "The crank pulley retaining bolt final torque is 125 ft-lb.",
            sha_char="b",
        ),
    )
    resolver = LibraryEvidenceConversationResolver(lambda query, limit: evidence)

    meaning = resolver(request())

    assert meaning.response_kind is ConversationMeaningKind.SYNTHESIS
    assert meaning.evidence_disposition == "corroborated"
    assert meaning.value == "170 N·m"
    assert meaning.source_labels == ("Factory Manual", "Service Reference")
    assert meaning.evidence_values == ("170 N·m", "125 ft-lb")
    assert "comparison:normalized-measurement" in meaning.qualifiers
    assert "library:item:manual_a" in meaning.source_refs
    assert "library:item:manual_b" in meaning.source_refs


def test_conflicting_measurements_are_preserved_instead_of_averaged():
    evidence = document(
        result(
            "manual_a",
            "Factory Manual",
            "Tighten the crank pulley bolt to 170 N·m.",
            sha_char="a",
        ),
        result(
            "manual_b",
            "Old Workshop Notes",
            "Tighten the crank pulley bolt to 140 N·m.",
            sha_char="b",
        ),
    )
    resolver = LibraryEvidenceConversationResolver(lambda query, limit: evidence)

    meaning = resolver(request())

    assert meaning.response_kind is ConversationMeaningKind.SYNTHESIS
    assert meaning.evidence_disposition == "conflicted"
    assert meaning.value is None
    assert meaning.evidence_values == ("170 N·m", "140 N·m")
    assert "comparison:measurement-conflict" in meaning.qualifiers


def test_strong_text_overlap_can_form_extractive_corroboration():
    evidence = document(
        result(
            "guide_a",
            "Guide A",
            "Disconnect battery power before removing the control module connector and inspect the connector for corrosion.",
            sha_char="a",
        ),
        result(
            "guide_b",
            "Guide B",
            "Before removing the control module connector disconnect battery power, then inspect the connector carefully for corrosion.",
            sha_char="b",
        ),
    )
    resolver = LibraryEvidenceConversationResolver(lambda query, limit: evidence)

    meaning = resolver(request("How should I inspect the control module connector?"))

    assert meaning.response_kind is ConversationMeaningKind.SYNTHESIS
    assert meaning.evidence_disposition == "corroborated"
    assert "comparison:lexical-overlap" in meaning.qualifiers
    assert "Disconnect battery power" in meaning.value


def test_unresolved_passages_remain_mixed_evidence():
    evidence = document(
        result(
            "guide_a",
            "Guide A",
            "Inspect the belt edge for fraying and glazing before installation.",
            sha_char="a",
        ),
        result(
            "guide_b",
            "Guide B",
            "The tensioner index mark should remain inside the reference window.",
            sha_char="b",
        ),
    )
    resolver = LibraryEvidenceConversationResolver(lambda query, limit: evidence)

    meaning = resolver(request("What should I check around the belt drive?"))

    assert meaning.response_kind is ConversationMeaningKind.SYNTHESIS
    assert meaning.evidence_disposition == "mixed"
    assert meaning.value is None
    assert "comparison:unresolved" in meaning.qualifiers
    assert len(meaning.evidence_values) == 2


def test_duplicate_chunks_from_one_item_do_not_fake_source_diversity():
    duplicate_a = result(
        "manual_a",
        "Factory Manual",
        "Tighten the crank pulley bolt to 170 N·m.",
        sha_char="a",
    )
    duplicate_b = dict(duplicate_a)
    duplicate_b["chunk_id"] = "chk_second"
    duplicate_b["snippet"] = "Final torque remains 170 N·m."
    resolver = LibraryEvidenceConversationResolver(
        lambda query, limit: document(duplicate_a, duplicate_b)
    )

    meaning = resolver(request())

    assert meaning.response_kind is ConversationMeaningKind.EVIDENCE
    assert meaning.source_label == "Factory Manual"


def test_multi_source_warning_posture_is_preserved():
    evidence = document(
        result(
            "manual_a",
            "Factory Manual",
            "Tighten the crank pulley bolt to 170 N·m.",
            sha_char="a",
        ),
        result(
            "manual_b",
            "Older Manual",
            "Tighten the crank pulley bolt to 170 N·m.",
            sha_char="b",
            warnings=("source_stale",),
        ),
    )
    resolver = LibraryEvidenceConversationResolver(lambda query, limit: evidence)

    meaning = resolver(request())

    assert meaning.evidence_disposition == "corroborated"
    assert "source-stale" in meaning.qualifiers
