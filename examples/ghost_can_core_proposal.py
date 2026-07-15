# SPDX-License-Identifier: GPL-3.0-only
"""Build a Core proposal and memory note from a Ghost CAN observation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from velvet.core.ghost_can import build_ghost_can_proposal, evaluate_ghost_can_proposal, summarize_ghost_can_observation

FIXTURE = Path(__file__).parent / "fixtures" / "ghost_can_core_observation.json"


def main() -> int:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    proposal = build_ghost_can_proposal(payload, actor="velvet-core-demo")
    decision = evaluate_ghost_can_proposal(proposal)
    memory = proposal.to_memory_record(receipt_id=decision.receipt_id)
    print(summarize_ghost_can_observation(payload))
    print("Court authorized description:", decision.authorized)
    print("Intent action:", proposal.to_intent().action)
    print("Memory kind:", memory.kind)
    print("Authority status:", memory.authority_status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
