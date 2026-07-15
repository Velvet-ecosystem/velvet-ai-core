# velvet/core/__init__.py
"""Shared Core primitives for Velvet."""

from .runtime import VelvetRuntime
from .module_loader import ModuleLoader
from .ghost_can import (
    GHOST_CAN_ACTION,
    GHOST_CAN_EVENT_TYPE,
    GHOST_CAN_TARGET,
    GhostCanProposal,
    build_ghost_can_proposal,
    evaluate_ghost_can_proposal,
    ghost_can_authority_context,
    ghost_can_memory_record,
    summarize_ghost_can_observation,
    validate_ghost_can_observation,
)

__all__ = [
    "VelvetRuntime",
    "ModuleLoader",
    "GHOST_CAN_ACTION",
    "GHOST_CAN_EVENT_TYPE",
    "GHOST_CAN_TARGET",
    "GhostCanProposal",
    "build_ghost_can_proposal",
    "evaluate_ghost_can_proposal",
    "ghost_can_authority_context",
    "ghost_can_memory_record",
    "summarize_ghost_can_observation",
    "validate_ghost_can_observation",
]
