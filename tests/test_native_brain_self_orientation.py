# SPDX-License-Identifier: GPL-3.0-only

import pytest

from velvet.core.native_brain.self_orientation import (
    NoDriftIntegrityGate,
    PersonalityProfile,
    PreferenceProfile,
    SelfIdentity,
    SelfOrientation,
)


def _orientation(**overrides):
    values = {
        "identity": SelfIdentity(),
        "personality": PersonalityProfile(traits={"patient": 0.9, "curious": 0.8}),
        "preferences": PreferenceProfile(values={"brief_updates": True}),
        "continuity_verified": True,
        "runtime_context_verified": True,
        "active_body": "founder-up2",
        "active_surface": "vehicle",
    }
    values.update(overrides)
    return SelfOrientation(**values)


def test_default_self_is_aligned_with_its_baseline():
    identity = SelfIdentity()
    report = NoDriftIntegrityGate(identity).evaluate(_orientation(identity=identity))

    assert report.aligned is True
    assert report.findings == ()


def test_preferences_can_change_without_identity_drift():
    identity = SelfIdentity()
    gate = NoDriftIntegrityGate(identity)
    changed = _orientation(
        identity=identity,
        preferences=PreferenceProfile(revision=2, values={"brief_updates": False}),
    )

    assert gate.evaluate(changed).aligned is True


def test_personality_profile_is_separate_and_bounded():
    with pytest.raises(ValueError):
        PersonalityProfile(traits={"patient": 1.2})

    profile = PersonalityProfile(revision=2, traits={"patient": 0.8})
    assert profile.revision == 2
    assert profile.traits["patient"] == 0.8


def test_identity_drift_blocks_cycle_alignment():
    baseline = SelfIdentity()
    changed = SelfIdentity(name="Not Velvet")
    report = NoDriftIntegrityGate(baseline).evaluate(_orientation(identity=changed))

    assert report.aligned is False
    assert "identity-drift" in {finding.code for finding in report.findings}


def test_unverified_continuity_or_runtime_context_blocks_alignment():
    gate = NoDriftIntegrityGate(SelfIdentity())
    report = gate.evaluate(
        _orientation(continuity_verified=False, runtime_context_verified=False)
    )

    assert report.aligned is False
    assert {finding.code for finding in report.findings} == {
        "continuity-unverified",
        "runtime-context-unverified",
    }


def test_orientation_summary_never_claims_authority():
    summary = _orientation().summary()

    assert summary["identity"] == "Velvet"
    assert summary["ready_for_reasoning"] is True
    assert summary["authority"] == "none"
