# SPDX-License-Identifier: GPL-3.0-only
"""Run Velvet Native Brain v0 against the public Ghost CAN fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from velvet.core.native_brain import run_native_brain_ghost_loop


def main() -> None:
    fixture = Path(__file__).parent / "fixtures" / "ghost_can_core_observation.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    result = run_native_brain_ghost_loop(payload)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
