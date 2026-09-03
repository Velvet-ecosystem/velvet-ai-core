from velvet.core.native_brain.conversation_ingress import (
    ConversationMeaningKind,
    ConversationWorkRequest,
)
from velvet.core.native_brain.library_evidence_conversation import (
    LibraryEvidenceConversationResolver,
)


def test_library_transport_failure_degrades_to_unavailable():
    def broken_provider(query, limit):
        raise OSError("librarian offline")

    resolver = LibraryEvidenceConversationResolver(broken_provider)
    request = ConversationWorkRequest(
        conversation_id="bench",
        turn_id="bench:1",
        turn_number=1,
        text="What torque should the pulley bolt use?",
        modality="text",
        audience="owner",
        act="question",
        strategy="answer",
        requires_authority_check=False,
        may_speak=True,
    )

    meaning = resolver(request)

    assert meaning.response_kind is ConversationMeaningKind.UNAVAILABLE
    assert "library-retrieval-unavailable" in meaning.qualifiers
