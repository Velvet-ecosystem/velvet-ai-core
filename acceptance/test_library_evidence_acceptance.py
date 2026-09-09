"""Real Runtime -> Core -> Language acceptance, with synthetic retrieval data.

Only the read-only Library client's response is supplied by the test. Runtime's
normalizer/composition, Core ingress/resolvers and Language gateway/realizer are
the production implementations. See the synthesis document for dependency pins.
"""

import json

import pytest

from services.library_conversation_provider import RuntimeLibraryEvidenceProvider
from services.local_conversation import build_local_conversation_gateway
from velvet.core.native_brain.conversation_ingress import handle_conversation_turn


GUIDANCE = (
    "Disconnect battery power before removing the control module connector "
    "and inspect the connector for corrosion."
)
TORQUE = "Tighten the crank pulley bolt to 170 N·m after seating the pulley."


class EvidenceClient:
    def __init__(self, snippets):
        self.calls = []
        self.results = [
            {
                "item_id": "manual_%d" % index,
                "chunk_id": "chunk_%d" % index,
                "title": "Synthetic manual %d" % index,
                "source": "acceptance-fixture",
                "trust_class": "primary",
                "sha256": str(index + 1) * 64,
                "score": 100.0 - index,
                "snippet": snippet,
                "retrieval_method": "full_text_deterministic",
                "lifecycle_state": "active",
                "warnings": [],
            }
            for index, snippet in enumerate(snippets)
        ]

    def evidence(self, query, limit):
        self.calls.append((query, limit))
        return {
            "schema": "velours.library.remote-evidence.v1",
            "read_only": True,
            "reference_only": True,
            "authority": "none",
            "evidence": {
                "reference_only": True,
                "canonical_receipt": False,
                "results": self.results,
            },
        }


def converse(tmp_path, snippets):
    snapshot = tmp_path / "body.json"
    snapshot.write_text(json.dumps({
        "schema": "velvet.runtime.body_state_snapshot.v1",
        "records": [],
        "read_only": True,
        "authority": "none",
        "actuation_granted": False,
        "actuation_performed": False,
    }), encoding="utf-8")
    client = EvidenceClient(snippets)
    meanings = []

    def capture_meaning(event, *, resolver):
        meaning = handle_conversation_turn(event, resolver=resolver)
        meanings.append(meaning)
        return meaning

    gateway = build_local_conversation_gateway(
        snapshot_path=snapshot,
        library_evidence_provider=RuntimeLibraryEvidenceProvider(client),
        handle_turn=capture_meaning,
    )
    exchange = gateway.submit("What guidance does the Library provide for this inspection?")
    assert len(client.calls) == 1
    assert len(meanings) == 1
    meaning = meanings[0]
    assert meaning["authority"] == "none"
    for flag in ("grants_authority", "grants_execution", "grants_actuation"):
        assert meaning[flag] is False
    assert exchange.reply.authority_granted is False
    return meaning, exchange.reply


@pytest.mark.parametrize("reverse", [False, True], ids=["original-rank", "reversed-rank"])
@pytest.mark.parametrize("snippets,disposition", [
    pytest.param((GUIDANCE, GUIDANCE.replace("battery power", "battery  power")),
                 "corroborated", id="A-genuine-guidance"),
    pytest.param((TORQUE, TORQUE.replace("170 N·m", "125 ft-lb")),
                 "corroborated", id="A-equivalent-units-same-claim"),
    pytest.param(("Do not tighten the crank pulley bolt to 170 N·m.",) * 2,
                 "corroborated", id="A-identical-negated-claim-retains-negation"),
    pytest.param((GUIDANCE, "Do not " + GUIDANCE[0].lower() + GUIDANCE[1:]),
                 "mixed", id="B-direct-negation"),
    pytest.param((GUIDANCE, GUIDANCE.replace("before", "after")),
                 "mixed", id="C-different-condition"),
    pytest.param((GUIDANCE, GUIDANCE.replace("control module", "audio module")),
                 "mixed", id="D-different-subject"),
    pytest.param((GUIDANCE, GUIDANCE.replace("Disconnect", "Connect")),
                 "mixed", id="D-different-predicate"),
    pytest.param((TORQUE, TORQUE.replace("crank pulley bolt", "alternator bracket bolt")),
                 "mixed", id="E-same-measurement-different-component"),
    pytest.param((TORQUE, TORQUE.replace("after seating", "before seating")),
                 "mixed", id="E-same-measurement-different-condition"),
    pytest.param((TORQUE, "Do not " + TORQUE[0].lower() + TORQUE[1:]),
                 "mixed", id="E-negated-measurement"),
    pytest.param((TORQUE, TORQUE.replace("170 N·m", "140 N·m")),
                 "conflicted", id="E-comparable-measurement-conflict"),
    pytest.param(("Inspect the belt edge for fraying and glazing before installation.",
                  "The tensioner index mark should remain inside the reference window."),
                 "mixed", id="F-unresolved"),
    pytest.param(("170 N·m", "170 N·m"), "mixed", id="F-no-component-or-condition"),
])
def test_library_evidence_through_real_composition(tmp_path, snippets, disposition, reverse):
    snippets = tuple(reversed(snippets)) if reverse else snippets
    meaning, reply = converse(tmp_path, snippets)

    assert meaning["response_kind"] == "synthesis"
    assert meaning["evidence_disposition"] == disposition
    assert "reference-only" in reply.qualifiers
    assert len(meaning["evidence_values"]) == len(snippets)
    assert tuple(meaning["evidence_values"]) == reply.evidence_texts
    assert tuple(meaning["source_refs"]) == reply.source_refs
    for index in range(len(snippets)):
        assert "library:item:manual_%d" % index in reply.source_refs
        assert "library:chunk:chunk_%d" % index in reply.source_refs
        assert "library:sha256:" + str(index + 1) * 64 in reply.source_refs
    if disposition == "corroborated":
        assert "They agree on" in reply.text or "They point to the same guidance" in reply.text
        if snippets[0].startswith("Do not"):
            assert "Do not tighten" in reply.text
            assert "comparison:normalized-measurement" not in reply.qualifiers
    else:
        assert meaning["value"] is None
        assert "They agree" not in reply.text
        assert "same guidance" not in reply.text
        assert "don't support one clean answer" in reply.text or "conflicting Library evidence" in reply.text
        if disposition == "mixed":
            assert tuple(snippets) == reply.evidence_texts


def test_third_source_disagreement_is_retained(tmp_path):
    meaning, reply = converse(tmp_path, (GUIDANCE, GUIDANCE, GUIDANCE.replace("before", "after")))
    assert meaning["evidence_disposition"] == "mixed"
    assert len(reply.evidence_texts) == 3
    assert "library:item:manual_2" in reply.source_refs
    assert "same guidance" not in reply.text


def test_no_evidence_cannot_become_agreement(tmp_path):
    meaning, reply = converse(tmp_path, ())
    assert meaning["response_kind"] == "unavailable"
    assert not reply.source_refs
    assert "They agree" not in reply.text
    assert "same guidance" not in reply.text
