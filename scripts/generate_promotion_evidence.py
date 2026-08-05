#!/usr/bin/env python3
"""Generate machine-readable module promotion evidence from one CI test run."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

SCHEMA = "velvet.promotion.evidence.v1"


def build_evidence(
    *,
    repository: str,
    module_id: str,
    suite: str,
    status: str,
    python_version: str,
    command: str = "python -m unittest discover",
    environment: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    env = os.environ if environment is None else environment
    normalized = (
        "passed"
        if str(status).strip() in {"0", "passed", "success"}
        else "failed"
    )
    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "repository": repository,
        "module_id": module_id,
        "suite": suite,
        "status": normalized,
        "commit_sha": env.get("GITHUB_SHA", "local"),
        "run_id": env.get("GITHUB_RUN_ID", "local"),
        "ref": env.get("GITHUB_REF_NAME", "local"),
        "python_version": python_version,
        "tests": {
            "command": command,
            "status": normalized,
        },
        "architecture_assertions": {
            "authority_granted_by_evidence": False,
            "simulated_input_may_unlock_physical_target": False,
        },
        "unresolved_risks": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--module", required=True, dest="module_id")
    parser.add_argument("--suite", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--python", required=True, dest="python_version")
    parser.add_argument("--command", default="python -m unittest discover")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    evidence = build_evidence(
        repository=args.repository,
        module_id=args.module_id,
        suite=args.suite,
        status=args.status,
        python_version=args.python_version,
        command=args.command,
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
