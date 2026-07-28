# SPDX-License-Identifier: GPL-3.0-only

import unittest

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


class NativeBrainSelfOrientationTests(unittest.TestCase):
    def test_default_self_is_aligned_with_its_baseline(self):
        identity = SelfIdentity()
        report = NoDriftIntegrityGate(identity).evaluate(_orientation(identity=identity))

        self.assertTrue(report.aligned)
        self.assertEqual(report.findings, ())

    def test_preferences_can_change_without_identity_drift(self):
        identity = SelfIdentity()
        gate = NoDriftIntegrityGate(identity)
        changed = _orientation(
            identity=identity,
            preferences=PreferenceProfile(revision=2, values={"brief_updates": False}),
        )

        self.assertTrue(gate.evaluate(changed).aligned)

    def test_personality_profile_is_separate_and_bounded(self):
        with self.assertRaises(ValueError):
            PersonalityProfile(traits={"patient": 1.2})

        profile = PersonalityProfile(revision=2, traits={"patient": 0.8})
        self.assertEqual(profile.revision, 2)
        self.assertEqual(profile.traits["patient"], 0.8)

    def test_identity_drift_blocks_cycle_alignment(self):
        baseline = SelfIdentity()
        changed = SelfIdentity(name="Not Velvet")
        report = NoDriftIntegrityGate(baseline).evaluate(_orientation(identity=changed))

        self.assertFalse(report.aligned)
        self.assertIn("identity-drift", {finding.code for finding in report.findings})

    def test_unverified_continuity_or_runtime_context_blocks_alignment(self):
        gate = NoDriftIntegrityGate(SelfIdentity())
        report = gate.evaluate(
            _orientation(continuity_verified=False, runtime_context_verified=False)
        )

        self.assertFalse(report.aligned)
        self.assertEqual(
            {finding.code for finding in report.findings},
            {"continuity-unverified", "runtime-context-unverified"},
        )

    def test_orientation_summary_never_claims_authority(self):
        summary = _orientation().summary()

        self.assertEqual(summary["identity"], "Velvet")
        self.assertTrue(summary["ready_for_reasoning"])
        self.assertEqual(summary["authority"], "none")


if __name__ == "__main__":
    unittest.main()
