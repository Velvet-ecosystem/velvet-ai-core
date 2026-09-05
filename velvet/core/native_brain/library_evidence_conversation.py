# SPDX-License-Identifier: GPL-3.0-only
"""Resolve owner questions from bounded read-only Velour Library evidence.

The resolver consumes a Runtime-normalized evidence bundle rather than importing
or reaching into Velour's Library directly. Retrieval remains reference-only:
matching or comparing passages does not promote them into canonical memory,
body state, doctrine, or execution authority.
"""

from __future__ import annotations

import re
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
MAX_LIBRARY_SOURCE_LABEL_CHARACTERS = 160
MAX_LIBRARY_WINDOW_CHUNKS = 3
MAX_SYNTHESIS_PASSAGES = 3
MAX_SYNTHESIS_EVIDENCE_CHARACTERS = 220

EvidenceProvider = Callable[[str, int], Mapping[str, Any]]

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_MEASUREMENT_RE = re.compile(
    r"(?<![A-Za-z0-9.])(-?\d+(?:\.\d+)?)\s*"
    r"(N\s*[·⋅.*-]?\s*m|ft\s*[-·⋅]?\s*lb|lb\s*[-·⋅]?\s*ft|"
    r"psi|kPa|MPa|bar|°\s*C|°C|°\s*F|°F|RPM|km\s*/\s*h|kph|mph|"
    r"mm|cm|inch(?:es)?|in|%|V|A)\b",
    re.IGNORECASE,
)

_STOPWORDS = frozenset(
    {
        "the", "and", "for", "that", "this", "with", "from", "into", "after",
        "before", "when", "where", "what", "which", "who", "why", "how", "does",
        "did", "has", "have", "had", "should", "would", "could", "can", "may",
        "use", "using", "used", "are", "was", "were", "is", "be", "been", "being",
        "to", "of", "on", "in", "at", "by", "or", "as", "an", "a", "it", "its",
    }
)

_FAMILY_TOLERANCE = {
    "torque": 2.0,
    "pressure": 2.0,
    "temperature": 1.0,
    "voltage": 0.2,
    "current": 0.2,
    "rpm": 50.0,
    "speed": 2.0,
    "length": 0.5,
    "percent": 1.0,
}


@dataclass(frozen=True)
class LibraryEvidenceRecord:
    item_id: str
    chunk_id: Optional[str]
    chunk_ids: Tuple[str, ...]
    windowed: bool
    window_truncated: bool
    title: str
    source: str
    trust_class: str
    sha256: str
    score: float
    snippet: str
    retrieval_method: str
    lifecycle_state: str
    warnings: Tuple[str, ...]


@dataclass(frozen=True)
class ComparableMeasurement:
    family: str
    base_value: float
    display: str


class LibraryEvidenceConversationResolver:
    """Return one passage or a bounded multi-source Library synthesis."""

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
            return _unavailable("library-retrieval-unavailable")

        passages = _answerable_passages(records)
        if not passages:
            return _unavailable("library-no-passage")
        if len(passages) == 1:
            return _single_evidence(passages[0])
        return _synthesize_evidence(query, passages)


def validate_library_evidence(document: Mapping[str, Any]) -> Tuple[LibraryEvidenceRecord, ...]:
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
    chunk_ids = _chunk_ids_from_mapping(item, chunk_id)
    windowed = item.get("windowed", False)
    window_truncated = item.get("window_truncated", False)
    if not isinstance(windowed, bool):
        raise ValueError("library evidence windowed must be boolean")
    if not isinstance(window_truncated, bool):
        raise ValueError("library evidence window_truncated must be boolean")
    if windowed and not chunk_ids:
        raise ValueError("windowed library evidence requires chunk_ids")
    if window_truncated and not windowed:
        raise ValueError("truncated library evidence must be windowed")
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
        chunk_ids=chunk_ids,
        windowed=windowed,
        window_truncated=window_truncated,
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


def _chunk_ids_from_mapping(
    item: Mapping[str, Any],
    chunk_id: Optional[str],
) -> Tuple[str, ...]:
    raw = item.get("chunk_ids")
    if raw is None:
        return (chunk_id,) if chunk_id else ()
    if not isinstance(raw, (list, tuple)):
        raise ValueError("library evidence chunk_ids must be a list or tuple")
    if len(raw) > MAX_LIBRARY_WINDOW_CHUNKS:
        raise ValueError("library evidence chunk_ids exceed resolver bound")
    clean = []
    for value in raw:
        candidate = _required_text_value("chunk_id", value)
        if candidate not in clean:
            clean.append(candidate)
    if chunk_id and chunk_id not in clean:
        raise ValueError("library evidence seed chunk must appear in chunk_ids")
    return tuple(clean)


def _answerable_passages(records: Sequence[LibraryEvidenceRecord]) -> Tuple[LibraryEvidenceRecord, ...]:
    passages = []
    seen_items = set()
    for record in records:
        if record.item_id in seen_items:
            continue
        if not record.chunk_ids or record.retrieval_method == "metadata" or not record.snippet.strip():
            continue
        passages.append(record)
        seen_items.add(record.item_id)
        if len(passages) >= MAX_SYNTHESIS_PASSAGES:
            break
    return tuple(passages)


def _single_evidence(passage: LibraryEvidenceRecord) -> GroundedConversationMeaning:
    qualifiers = [
        "reference-only",
        "trust-class:%s" % passage.trust_class,
        "retrieval:%s" % passage.retrieval_method,
    ]
    if passage.windowed:
        qualifiers.append("evidence-window:contiguous")
    if passage.window_truncated:
        qualifiers.append("evidence-window:truncated")
    qualifiers.extend(_source_warning_qualifiers((passage,)))
    return GroundedConversationMeaning(
        response_kind=ConversationMeaningKind.EVIDENCE,
        confidence=1.0,
        fact_id="library.evidence",
        value=_bounded_excerpt(passage.snippet),
        source_label=_bounded_source_label(passage.title),
        qualifiers=tuple(qualifiers),
        source_refs=_stable_refs((passage,)),
    )


def _synthesize_evidence(
    query: str,
    passages: Sequence[LibraryEvidenceRecord],
) -> GroundedConversationMeaning:
    labels = tuple(_bounded_source_label(passage.title) for passage in passages)
    refs = _stable_refs(passages)
    qualifiers = ["reference-only", "multi-source"]
    if any(passage.windowed for passage in passages):
        qualifiers.append("evidence-window:contiguous")
    if any(passage.window_truncated for passage in passages):
        qualifiers.append("evidence-window:truncated")
    qualifiers.extend(_source_warning_qualifiers(passages))

    measurements = tuple(_measurement_for_query(passage.snippet, query) for passage in passages)
    if all(measurement is not None for measurement in measurements):
        concrete = tuple(measurement for measurement in measurements if measurement is not None)
        families = {measurement.family for measurement in concrete}
        if len(families) == 1:
            values = tuple(measurement.display for measurement in concrete)
            if _measurements_agree(concrete):
                qualifiers.append("comparison:normalized-measurement")
                return GroundedConversationMeaning(
                    response_kind=ConversationMeaningKind.SYNTHESIS,
                    confidence=1.0,
                    fact_id="library.synthesis",
                    value=concrete[0].display,
                    source_labels=labels,
                    evidence_values=values,
                    evidence_disposition="corroborated",
                    qualifiers=tuple(qualifiers),
                    source_refs=refs,
                )
            qualifiers.append("comparison:measurement-conflict")
            return GroundedConversationMeaning(
                response_kind=ConversationMeaningKind.SYNTHESIS,
                confidence=1.0,
                fact_id="library.synthesis",
                source_labels=labels,
                evidence_values=values,
                evidence_disposition="conflicted",
                qualifiers=tuple(qualifiers),
                source_refs=refs,
            )

    evidence_values = tuple(_bounded_synthesis_evidence(passage.snippet) for passage in passages)
    if _minimum_content_similarity(passages, query) >= 0.45:
        qualifiers.append("comparison:lexical-overlap")
        return GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.SYNTHESIS,
            confidence=1.0,
            fact_id="library.synthesis",
            value=_bounded_excerpt(passages[0].snippet),
            source_labels=labels,
            evidence_values=evidence_values,
            evidence_disposition="corroborated",
            qualifiers=tuple(qualifiers),
            source_refs=refs,
        )

    qualifiers.append("comparison:unresolved")
    return GroundedConversationMeaning(
        response_kind=ConversationMeaningKind.SYNTHESIS,
        confidence=1.0,
        fact_id="library.synthesis",
        source_labels=labels,
        evidence_values=evidence_values,
        evidence_disposition="mixed",
        qualifiers=tuple(qualifiers),
        source_refs=refs,
    )


def _measurement_for_query(text: str, query: str) -> Optional[ComparableMeasurement]:
    matches = []
    for match in _MEASUREMENT_RE.finditer(text):
        measurement = _normalize_measurement(match.group(1), match.group(2), match.group(0))
        if measurement is not None:
            matches.append(measurement)
    if not matches:
        return None
    hinted_family = _query_family_hint(query)
    if hinted_family is not None:
        for measurement in matches:
            if measurement.family == hinted_family:
                return measurement
    return matches[0]


def _normalize_measurement(number_text: str, unit_text: str, display_text: str) -> Optional[ComparableMeasurement]:
    try:
        value = float(number_text)
    except ValueError:
        return None
    unit = unit_text.casefold()
    compact = (
        unit.replace(" ", "")
        .replace("·", "")
        .replace("⋅", "")
        .replace("*", "")
        .replace("-", "")
        .replace("°", "")
    )

    if compact == "nm":
        family, base = "torque", value
    elif compact in {"ftlb", "lbft"}:
        family, base = "torque", value * 1.3558179483314
    elif compact == "psi":
        family, base = "pressure", value * 6.894757293168
    elif compact == "kpa":
        family, base = "pressure", value
    elif compact == "mpa":
        family, base = "pressure", value * 1000.0
    elif compact == "bar":
        family, base = "pressure", value * 100.0
    elif compact == "c":
        family, base = "temperature", value
    elif compact == "f":
        family, base = "temperature", (value - 32.0) * 5.0 / 9.0
    elif compact == "v":
        family, base = "voltage", value
    elif compact == "a":
        family, base = "current", value
    elif compact == "rpm":
        family, base = "rpm", value
    elif compact in {"km/h", "kph"}:
        family, base = "speed", value
    elif compact == "mph":
        family, base = "speed", value * 1.609344
    elif compact == "mm":
        family, base = "length", value
    elif compact == "cm":
        family, base = "length", value * 10.0
    elif compact in {"in", "inch", "inches"}:
        family, base = "length", value * 25.4
    elif compact == "%":
        family, base = "percent", value
    else:
        return None

    return ComparableMeasurement(
        family=family,
        base_value=base,
        display=" ".join(display_text.split()),
    )


def _query_family_hint(query: str) -> Optional[str]:
    lower = query.casefold()
    hints = (
        ("torque", ("torque", "tighten", "tightening", "bolt", "nut")),
        ("pressure", ("pressure", "psi", "kpa", "bar")),
        ("temperature", ("temperature", "temp", "hot", "cold")),
        ("voltage", ("voltage", "volt")),
        ("current", ("current", "amp", "amper")),
        ("rpm", ("rpm", "engine speed")),
        ("speed", ("speed", "mph", "km/h", "kph")),
        ("length", ("length", "width", "height", "clearance", "gap", "diameter")),
        ("percent", ("percent", "percentage", "%")),
    )
    for family, phrases in hints:
        if any(phrase in lower for phrase in phrases):
            return family
    return None


def _measurements_agree(measurements: Sequence[ComparableMeasurement]) -> bool:
    if not measurements:
        return False
    family = measurements[0].family
    if any(measurement.family != family for measurement in measurements):
        return False
    values = [measurement.base_value for measurement in measurements]
    spread = max(values) - min(values)
    scale = max(max(abs(value) for value in values), 1.0)
    tolerance = max(_FAMILY_TOLERANCE.get(family, 0.0), scale * 0.02)
    return spread <= tolerance


def _minimum_content_similarity(
    passages: Sequence[LibraryEvidenceRecord], query: str
) -> float:
    token_sets = [_content_tokens(passage.snippet, query) for passage in passages]
    if any(len(tokens) < 4 for tokens in token_sets):
        return 0.0
    scores = []
    for index, left in enumerate(token_sets):
        for right in token_sets[index + 1 :]:
            union = left | right
            scores.append(len(left & right) / float(len(union)) if union else 0.0)
    return min(scores) if scores else 0.0


def _content_tokens(text: str, query: str) -> set[str]:
    query_tokens = {
        token.casefold()
        for token in _WORD_RE.findall(query)
        if len(token) >= 3 and token.casefold() not in _STOPWORDS
    }
    tokens = {
        token.casefold()
        for token in _WORD_RE.findall(text)
        if len(token) >= 3 and token.casefold() not in _STOPWORDS
    }
    reduced = tokens - query_tokens
    return reduced or tokens


def _stable_refs(passages: Sequence[LibraryEvidenceRecord]) -> Tuple[str, ...]:
    refs = []
    for passage in passages:
        candidates = [
            "library:item:%s" % passage.item_id,
            "library:sha256:%s" % passage.sha256,
        ]
        candidates.extend("library:chunk:%s" % chunk_id for chunk_id in passage.chunk_ids)
        for candidate in candidates:
            if candidate not in refs:
                refs.append(candidate)
    return tuple(refs)


def _source_warning_qualifiers(passages: Sequence[LibraryEvidenceRecord]) -> Tuple[str, ...]:
    stale = False
    superseded = False
    for passage in passages:
        warning_set = {warning.casefold() for warning in passage.warnings}
        stale = stale or "source_stale" in warning_set or "freshness_deadline_passed" in warning_set
        superseded = superseded or "source_superseded" in warning_set or passage.lifecycle_state == "superseded"
    qualifiers = []
    if stale:
        qualifiers.append("source-stale")
    if superseded:
        qualifiers.append("source-superseded")
    return tuple(qualifiers)


def _bounded_excerpt(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= MAX_LIBRARY_EXCERPT_CHARACTERS:
        return clean
    return clean[: MAX_LIBRARY_EXCERPT_CHARACTERS - 1].rstrip() + "…"


def _bounded_synthesis_evidence(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= MAX_SYNTHESIS_EVIDENCE_CHARACTERS:
        return clean
    return clean[: MAX_SYNTHESIS_EVIDENCE_CHARACTERS - 1].rstrip() + "…"


def _bounded_source_label(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= MAX_LIBRARY_SOURCE_LABEL_CHARACTERS:
        return clean
    return clean[: MAX_LIBRARY_SOURCE_LABEL_CHARACTERS - 1].rstrip() + "…"


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
