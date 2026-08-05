import unittest

from velvet.core.dream_state_policy import (
    MemoryTask,
    MemoryTempo,
    decide_memory_task,
)


class TestDreamStatePolicy(unittest.TestCase):
    def test_quiet_phase_can_prepare_but_not_adopt_permanent_memory(self):
        result = decide_memory_task(
            MemoryTask.PERMANENT_MEMORY_ADOPTION,
            current_tempo=MemoryTempo.QUIET,
            physical_presence_verified=False,
            power_allows_background_work=True,
        )
        self.assertFalse(result.allowed)
        self.assertTrue(result.prepare_only)
        self.assertEqual(result.refusal_reason, "owner_presence_required")
        self.assertFalse(result.authority_granted)

    def test_index_build_requires_quiet_power_window(self):
        result = decide_memory_task(
            MemoryTask.INDEX_BUILD,
            current_tempo=MemoryTempo.ACTIVE,
            physical_presence_verified=True,
            power_allows_background_work=True,
        )
        self.assertFalse(result.allowed)

    def test_presence_phase_allows_reviewed_trust_change(self):
        result = decide_memory_task(
            MemoryTask.DOCTRINE_CHANGE,
            current_tempo=MemoryTempo.PRESENCE_REQUIRED,
            physical_presence_verified=True,
            power_allows_background_work=True,
        )
        self.assertTrue(result.allowed)
        self.assertFalse(result.authority_granted)


if __name__ == "__main__":
    unittest.main()
