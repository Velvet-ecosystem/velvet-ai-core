# SPDX-License-Identifier: GPL-3.0-only
"""First preserved Native Brain v0 loop.

observation -> safety -> state -> priority -> Ruby -> Velour -> memory -> response

It does not grant authority, select executors, touch hardware, or bypass Runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping

from velvet.core.ghost_can import (
    GHOST_CAN_EVENT_TYPE,
    summarize_ghost_can_observation,
    validate_ghost_can_observation,
)

from .brainstem import BrainstemDecision, BrainstemRouter
from .conversation import render_no_llm_ghost_response
from .handmaiden_stem import StemResult
from .memory import NativeMemoryNote
from .safety import authority_report, validate_no_authority_payload
from .state import NativeBrainState
from .stems import RubyStem, VelourStem


@dataclass(frozen=True)
class NativeBrainResult:
    event_type: str
    attention: BrainstemDecision
    state: NativeBrainState
    stems: List[StemResult]
    memory_note: NativeMemoryNote
    authority: Dict[str, bool]
    response: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "native_brain_response",
            "event_type": self.event_type,
            "attention": self.attention.to_dict(),
            "state": self.state.to_dict(),
            "stems_consulted": [stem.stem for stem in self.stems if stem.domain_match],
            "stem_results": [stem.to_dict() for stem in self.stems],
            "memory_note": self.memory_note.to_dict(),
            "authority": dict(self.authority),
            "response": self.response,
        }


def run_native_brain_ghost_loop(payload: Mapping[str, Any]) -> NativeBrainResult:
    validate_no_authority_payload(payload)
    observation = validate_ghost_can_observation(payload)

    state = NativeBrainState()
    state.update_from_ghost_observation(observation)

    attention = BrainstemRouter().assess(observation)
    state.attention_state = attention.priority

    stems = [RubyStem().interpret(observation), VelourStem().interpret(observation)]

    memory_note = NativeMemoryNote(
        kind="observation_only",
        source_event_type=GHOST_CAN_EVENT_TYPE,
        summary=summarize_ghost_can_observation(observation),
        stems=[stem.stem for stem in stems if stem.domain_match],
        public_safe=True,
        authority_requested=False,
        authority_granted=False,
        continuity_candidate=True,
        tags=["native-brain-v0", "ghost-can", "read-only", "no-authority"],
    )

    return NativeBrainResult(
        event_type=GHOST_CAN_EVENT_TYPE,
        attention=attention,
        state=state,
        stems=stems,
        memory_note=memory_note,
        authority=authority_report(),
        response=render_no_llm_ghost_response(observation),
    )
