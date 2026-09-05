import unittest

from velvet.core.native_brain.conversation_ingress import (
    ConversationMeaningKind,
    ConversationWorkRequest,
)
from velvet.core.native_brain.library_evidence_conversation import (
    LIBRARY_EVIDENCE_SCHEMA,
    LibraryEvidenceConversationResolver,
    validate_library_evidence,
)


def _request(text="What are Velour Library's core principles?"):
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


def _document(**result_overrides):
    result = {
        "item_id": "item_readme",
        "chunk_id": "chk_1",
        "title": "Velour Library README",
        "source": "Velvet ecosystem repository",
        "trust_class": "primary",
        "sha256": "a" * 64,
        "score": 4.0,
        "snippet": "## Core principles - Local first. - Preserve the source.",
        "retrieval_method": "full_text_deterministic",
        "lifecycle_state": "active",
        "warnings": [],
    }
    result.update(result_overrides)
    return {
        "schema": LIBRARY_EVIDENCE_SCHEMA,
        "query": "What are Velour Library's core principles?",
        "read_only": True,
        "reference_only": True,
        "authority": "none",
        "results": [result],
    }


class LibraryEvidenceWindowContractTests(unittest.TestCase):
    def test_window_retains_all_chunk_refs_and_qualifier(self):
        document = _document(
            chunk_ids=["chk_1", "chk_2", "chk_3"],
            windowed=True,
            window_truncated=False,
            snippet=(
                "## Core principles - Local first. - Provenance before confidence. "
                "- Preserve the source. - Trust is graded. - Retrieval is not belief. "
                "- Receipts matter. - Knowledge is modular. - Models are optional. "
                "- Currency is metadata, not truth."
            ),
        )
        resolver = LibraryEvidenceConversationResolver(lambda query, limit: document)

        meaning = resolver(_request())

        self.assertEqual(meaning.response_kind, ConversationMeaningKind.EVIDENCE)
        self.assertIn("Currency is metadata, not truth", meaning.value)
        self.assertIn("evidence-window:contiguous", meaning.qualifiers)
        self.assertEqual(
            meaning.source_refs,
            (
                "library:item:item_readme",
                "library:sha256:" + "a" * 64,
                "library:chunk:chk_1",
                "library:chunk:chk_2",
                "library:chunk:chk_3",
            ),
        )

    def test_truncated_window_is_explicit(self):
        resolver = LibraryEvidenceConversationResolver(
            lambda query, limit: _document(
                chunk_ids=["chk_1", "chk_2"],
                windowed=True,
                window_truncated=True,
            )
        )
        meaning = resolver(_request())
        self.assertIn("evidence-window:truncated", meaning.qualifiers)

    def test_window_shape_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "chunk_ids exceed"):
            validate_library_evidence(
                _document(
                    chunk_ids=["chk_1", "chk_2", "chk_3", "chk_4"],
                    windowed=True,
                )
            )
        with self.assertRaisesRegex(ValueError, "seed chunk"):
            validate_library_evidence(
                _document(chunk_ids=["chk_other"], windowed=True)
            )
        with self.assertRaisesRegex(ValueError, "must be windowed"):
            validate_library_evidence(_document(window_truncated=True))

    def test_legacy_single_chunk_result_stays_compatible(self):
        records = validate_library_evidence(_document())
        self.assertEqual(records[0].chunk_ids, ("chk_1",))
        self.assertFalse(records[0].windowed)


if __name__ == "__main__":
    unittest.main()
