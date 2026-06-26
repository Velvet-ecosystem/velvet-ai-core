# SPDX-License-Identifier: GPL-3.0-only
"""Read-only local memory inspection commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from velvet.core.memory.associations import MemoryAssociationIndex
from velvet.core.memory.retrieval import MemoryRetrievalService


def load_records(path: str) -> List[Dict[str, Any]]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".jsonl":
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        records = json.loads(text)
    if not isinstance(records, list):
        raise ValueError("memory source must contain a list of records")
    if any(not isinstance(record, dict) for record in records):
        raise ValueError("memory source entries must be objects")
    MemoryRetrievalService(records)
    return records


def recall(records: Iterable[Dict[str, Any]], event_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    results = MemoryRetrievalService(records).retrieve(event_id, limit=limit)
    return [
        {
            "event_id": item.score.event_id,
            "score": item.score.score,
            "association": item.score.association,
            "confidence": item.score.confidence,
            "salience": item.score.salience,
            "authority_weight": item.score.authority_weight,
        }
        for item in results
    ]


def neighbours(records: Iterable[Dict[str, Any]], event_id: str) -> Dict[str, Any]:
    snapshot = list(records)
    MemoryRetrievalService(snapshot)
    index = MemoryAssociationIndex()
    index.add_records(snapshot)
    return {
        "event_id": event_id,
        "forward": index.forward_links(event_id),
        "backlinks": index.backlinks(event_id),
        "neighbours": index.neighbours(event_id),
    }


def verify(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    snapshot = list(records)
    MemoryRetrievalService(snapshot)
    return {"valid": True, "record_count": len(snapshot), "mode": "read-only"}


def explain(records: Iterable[Dict[str, Any]], event_id: str, limit: int = 10) -> Dict[str, Any]:
    return {
        "query_event_id": event_id,
        "ranking": "association 45%, salience 30%, confidence 20%, authority status 5%",
        "results": recall(records, event_id, limit=limit),
        "truth_claimed": False,
        "authority_granted": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="velvet")
    subcommands = parser.add_subparsers(dest="area", required=True)
    memory = subcommands.add_parser("memory")
    memory.add_argument("--source", required=True, help="JSON or JSONL memory record file")
    actions = memory.add_subparsers(dest="action", required=True)

    for name in ("recall", "explain"):
        command = actions.add_parser(name)
        command.add_argument("event_id")
        command.add_argument("--limit", type=int, default=10)

    command = actions.add_parser("neighbours")
    command.add_argument("event_id")
    actions.add_parser("verify")
    return parser


def _run(args) -> Dict[str, Any]:
    records = load_records(args.source)
    if args.action == "recall":
        return recall(records, args.event_id, args.limit)
    if args.action == "explain":
        return explain(records, args.event_id, args.limit)
    if args.action == "neighbours":
        return neighbours(records, args.event_id)
    return verify(records)


def main(argv=None) -> int:
    try:
        args = build_parser().parse_args(argv)
        output = _run(args)
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        error = {
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
            "ok": False,
        }
        print(json.dumps(error, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
