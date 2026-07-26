# SPDX-License-Identifier: GPL-3.0-only
"""Inert compatibility adapter for Velvet Runtime's AI Core presence probe.

This adapter intentionally accepts no dependencies, stores no Runtime
references, exposes no attachment path, and performs no work. Its sole purpose
is to let Runtime verify that the advisory AI Core package is installed while
preserving the brain-isolation boundary.
"""

from __future__ import annotations


class BrainAdapter:
    """Presence-only adapter with no authority or Runtime connectivity."""

    __slots__ = ()

    def __init__(self) -> None:
        """Construct an inert AI Core presence marker."""
