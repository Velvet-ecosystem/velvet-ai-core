import unittest

from velvet.core.presence_fusion import (
    PresenceObservation,
    PresencePurpose,
    fuse_presence,
)


def observation(source, **overrides):
    values = dict(
        presence_source=source,
        spatial_presence_source=source,
        zone="driver-seat",
        timestamp=10.0,
        fresh_until=20.0,
        confidence=0.9,
        range_confidence=0.9,
        living_motion_detected=True,
        owner_match_confidence=0.9,
        spoofing_risk=0.1,
        permitted_purposes=(PresencePurpose.ACCESS, PresencePurpose.SAFETY),
    )
    values.update(overrides)
    return PresenceObservation(**values)


class TestPresenceFusion(unittest.TestCase):
    def test_access_requires_source_diversity(self):
        result = fuse_presence(
            [observation("nfc")],
            purpose=PresencePurpose.ACCESS,
            zone="driver-seat",
            now=12.0,
        )
        self.assertFalse(result.source_diversity_met)
        self.assertEqual(result.confidence, 0.0)
        self.assertFalse(result.authority_granted)

    def test_stale_observation_is_rejected(self):
        result = fuse_presence(
            [observation("nfc", fresh_until=11.0), observation("seat-radar")],
            purpose=PresencePurpose.SAFETY,
            zone="driver-seat",
            now=12.0,
        )
        self.assertIn(("nfc", "stale"), result.rejected_sources)
        self.assertFalse(result.source_diversity_met)

    def test_two_fresh_sources_can_produce_confidence_not_authority(self):
        result = fuse_presence(
            [observation("nfc"), observation("seat-radar")],
            purpose=PresencePurpose.ACCESS,
            zone="driver-seat",
            now=12.0,
        )
        self.assertTrue(result.source_diversity_met)
        self.assertGreater(result.confidence, 0.0)
        self.assertFalse(result.authority_granted)


if __name__ == "__main__":
    unittest.main()
