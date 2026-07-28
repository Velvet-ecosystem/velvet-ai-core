# SPDX-License-Identifier: GPL-3.0-only
"""Velvet Native Brain experimental local-cognition subsystem."""

from .attention import (
    AttentionAssessment,
    AttentionContext,
    AttentionEngine,
    ObservationMaturity,
)
from .brainstem import BrainstemDecision, BrainstemRouter
from .cognition import CognitiveDecision, CognitiveOutcome, ObservationEnvelope
from .conversation import render_no_llm_ghost_response
from .curiosity import (
    CuriosityAssessment,
    CuriosityContext,
    CuriosityDisposition,
    CuriosityEngine,
    CuriosityThreadCandidate,
)
from .cycle import (
    CognitiveCycle,
    CognitiveCycleResult,
    CognitiveKey,
    CycleStage,
    CycleTraceEntry,
    KeyState,
)
from .handmaiden_stem import HandmaidenStem, StemResult
from .llm_adapter import LLMPolishRequest, OptionalLLMAdapter
from .memory import NativeMemoryNote
from .native_loop import NativeBrainResult, run_native_brain_ghost_loop
from .presence import PresenceContext, PresenceGate
from .safety import NativeBrainSafetyError, authority_report, validate_no_authority_payload
from .self_orientation import (
    IntegrityFinding,
    IntegrityReport,
    NoDriftIntegrityGate,
    PersonalityProfile,
    PreferenceProfile,
    SelfIdentity,
    SelfOrientation,
)
from .state import NativeBrainState
from .stems import RubyStem, VelourStem
from .working_state import DeferredThought, OpenThread, ThreadStatus

__all__ = [
    "AttentionAssessment",
    "AttentionContext",
    "AttentionEngine",
    "BrainstemDecision",
    "BrainstemRouter",
    "CognitiveCycle",
    "CognitiveCycleResult",
    "CognitiveDecision",
    "CognitiveKey",
    "CognitiveOutcome",
    "CuriosityAssessment",
    "CuriosityContext",
    "CuriosityDisposition",
    "CuriosityEngine",
    "CuriosityThreadCandidate",
    "CycleStage",
    "CycleTraceEntry",
    "DeferredThought",
    "HandmaidenStem",
    "IntegrityFinding",
    "IntegrityReport",
    "KeyState",
    "LLMPolishRequest",
    "NativeBrainResult",
    "NativeBrainSafetyError",
    "NativeBrainState",
    "NativeMemoryNote",
    "NoDriftIntegrityGate",
    "ObservationEnvelope",
    "ObservationMaturity",
    "OpenThread",
    "OptionalLLMAdapter",
    "PersonalityProfile",
    "PreferenceProfile",
    "PresenceContext",
    "PresenceGate",
    "RubyStem",
    "SelfIdentity",
    "SelfOrientation",
    "StemResult",
    "ThreadStatus",
    "VelourStem",
    "authority_report",
    "render_no_llm_ghost_response",
    "run_native_brain_ghost_loop",
    "validate_no_authority_payload",
]
