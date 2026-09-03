# SPDX-License-Identifier: GPL-3.0-only
"""Resolve owner questions from bounded read-only Velour Library evidence.

The resolver consumes a Runtime-normalized evidence bundle rather than importing
or reaching into Velour's Library directly. Retrieval remains reference-only:
matching a passage does not promote that passage into canonical memory, body
state, doctrine, or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple

from .conversation_ingress import (
    ConversationMeaningKind,
    ConversationWorkRequest,
    GroundedConversationMeaning,
)

LIBRARY_EVIDENCE_SCHEMA = "velvet.runtime.library_evidence.v1"
MAX_LIBRARY_QUERY_CHARACTERS = 512
MAX_LIBRARY_RESULTS = 20
MAX_LIBRARY_EXCERPT_CHARACTERS = 480

EvidenceProvider = Callable[[str, int], Mapping[str, Any]]


@dataclass(frozen=True)
class LibraryEvidenceRecord:
    item_id: str
    chunk_id: Optional[str]
    title: str
    source: str
    trust_class: str
    sha256: str
    score: float
    snippet: str
    retrieval_method: str
    lifecycle_state: str
    warnings: Tuple[str, ...]


class LibraryEvidenceConversationResolver:
    """Return one provenance-backed Library passage for informational questions."""

    def __init__(self, evidence_provider: EvidenceProvider, *, limit: int = 5) -> None:
        if not callable(evidence_provider):
            raise TypeError("evidence_provider must be callable")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIBRARY_RESULTS:
            raise ValueError("limit must be an integer between 1 and %d" % MAX_LIBRARY_RESULTS)
        self._evidence_provider = evidence_provider
        self._limit = limit

    def __call__(self, request: ConversationWorkRequest) -> GroundedConversationMeaning:
        if not isinstance(request, ConversationWorkRequest):
            raise TypeError("request must be ConversationWorkRequest")

        if request.requires_authority_check:
            return GroundedConversationMeaning(
                response_kind=ConversationMeaningKind.AUTHORITY_REQUIRED,
                confidence=1.0,
                qualifiers=("runtime-authorization-required",),
            )

        if request.act != "question":
            return _unavailable("library-question-not-requested")

        query = " ".join(request.text.split())
        if len(query) > MAX_LIBRARY_QUERY_CHARACTERS:
            return _unavailable("library-query-too-long")

        try:
            document = self._evidence_provider(query, self._limit)
            records = validate_library_evidence(document)
        except Exception:
            # A sleeping/offline librarian is a missing evidence source, not a
            # reason to crash the shared conversation path or body grounding.
            return _unavailable("library-retrieval-unavailable")

        passage = _best_passage(records)
        if passage is None:
            return _unavailable("library-no-passage")

        qualifiers = [
            "reference-only",
            "trust-class:%s" % passage.trust_class,
            "retrieval:%s" % passage.retrieval_method,
        ]
        warning_set = {warning.casefold() for warning in passage.warnings}
        if "source_stale" in warning_set or "freshness_deadline_passed" in warning_set:
            qualifiers.append("source-stale")
        if "source_superseded" in warning_set or passage.lifecycle_state == "superseded":
            qualifiers.append("source-superseded")

        refs = [
            "library:item:%s" % passage.item_id,
            "library:sha256:%s" % passage.sha256,
        ]
        if passage.chunk_id:
            refs.append("library:chunk:%s" % passage.chunk_id)

        return GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.EVIDENCE,
            confidence=1.0,
            fact_id="library.evidence",
            value=_bounded_excerpt(passage.snippet),
            source_label=passage.title,
            qualifiers=tuple(qualifiers),
            source_refs=tuple(refs),
        )


def validate_library_evidence(document: Mapping[str, Any]) -> Tuple[LibraryEvidenceRecord, ...]:
    """Validate Runtime's normalized Library retrieval posture."""

    if not isinstance(document, Mapping):
        raise TypeError("library evidence must be a mapping")
    if document.get("schema") != LIBRARY_EVIDENCE_SCHEMA:
        raise ValueError("unsupported library evidence schema")
    if document.get("read_only") is not True:
        raise ValueError("library evidence must be read-only")
    if document.get("reference_only") is not True:
        raise ValueError("library evidence must remain reference-only")
    if document.get("authority") != "none":
        raise ValueError("library evidence cannot carry authority")
    results = document.get("results")
    if not isinstance(results, list):
        raise ValueError("library evidence results must be a list")
    if len(results) > MAX_LIBRARY_RESULTS:
        raise ValueError("library evidence result count exceeds resolver bound")

    return tuple(_record_from_mapping(item) for item in results)


def _record_from_mapping(item: Any) -> LibraryEvidenceRecord:
    if not isinstance(item, Mapping):
        raise ValueError("library evidence result must be a mapping")
    item_id = _required_text(item, "item_id")
    title = _required_text(item, "title")
    source = _required_text(item, "source")
    trust_class = _required_text(item, "trust_class")
    sha256 = _required_text(item, "sha256")
    if len(sha256) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in sha256):
        raise ValueError("library evidence sha256 must be a 64-character hexadecimal digest")
    snippet = _required_text(item, "snippet")
    retrieval_method = _required_text(item, "retrieval_method")
    lifecycle_state = _required_text(item, "lifecycle_state")
    chunk_raw = item.get("chunk_id")
    chunk_id = None if chunk_raw is None else _required_text_value("chunk_id", chunk_raw)
    score_raw = item.get("score")
    if isinstance(score_raw, bool) or not isinstance(score_raw, (int, float)):
        raise ValueError("library evidence score must be numeric")
    warnings_raw = item.get("warnings", [])
    if not isinstance(warnings_raw, (list, tuple)):
        raise ValueError("library evidence warnings must be a list or tuple")
    warnings = tuple(_required_text_value("warning", warning) for warning in warnings_raw)
    return LibraryEvidenceRecord(
        item_id=item_id,
        chunk_id=chunk_id,
        title=title,
        source=source,
        trust_class=trust_class,
        sha256=sha256.lower(),
        score=float(score_raw),
        snippet=snippet,
        retrieval_method=retrieval_method,
        lifecycle_state=lifecycle_state,
        warnings=warnings,
    )


def _best_passage(records: Sequence[LibraryEvidenceRecord]) -> Optional[LibraryEvidenceRecord]:
    # Metadata-only hits can tell us that a document exists, but they are not a
    # passage that Velvet can safely quote back as an answer.
    for record in records:
        if record.chunk_id and record.retrieval_method != "metadata" and record.snippet.strip():
            return record
    return None


def _bounded_excerpt(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= MAX_LIBRARY_EXCERPT_CHARACTERS:
        return clean
    clipped = clean[: MAX_LIBRARY_EXCERPT_CHARACTERS - 1].rstrip()
    return clipped + "…"


def _required_text(item: Mapping[str, Any], key: str) -> str:
    return _required_text_value(key, item.get(key))


def _required_text_value(label: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be non-empty text" % label)
    return value.strip()


def _unavailable(reason: str) -> GroundedConversationMeaning:
    return GroundedConversationMeaning(
        response_kind=ConversationMeaningKind.UNAVAILABLE,
        confidence=0.0,
        qualifiers=(reason,),
    )
