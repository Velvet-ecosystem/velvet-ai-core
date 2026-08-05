import unittest

from velvet.core.model_capabilities import (
    ModelCapabilityRegistry,
    ModelCapabilitySpec,
)


class TestModelCapabilities(unittest.TestCase):
    def setUp(self):
        self.registry = ModelCapabilityRegistry()
        self.registry.register(
            ModelCapabilitySpec(
                capability_name="memory-summarizer",
                preferred_local_engine="local-summary-engine",
                fallback_engine="hosted-summary-engine",
                offline_available=True,
                cloud_permission_required=True,
                max_authority_level=0,
                data_retention_rule="local-only",
                receipt_required=True,
                refusal_behavior="capability_unavailable",
            )
        )

    def test_local_engine_is_preferred(self):
        result = self.registry.select(
            "memory-summarizer",
            local_engine_available=True,
            fallback_engine_available=True,
            cloud_permission=False,
        )
        self.assertEqual(result.engine, "local-summary-engine")
        self.assertFalse(result.used_fallback)
        self.assertFalse(result.authority_granted)

    def test_cloud_fallback_requires_permission(self):
        result = self.registry.select(
            "memory-summarizer",
            local_engine_available=False,
            fallback_engine_available=True,
            cloud_permission=False,
        )
        self.assertFalse(result.available)
        self.assertEqual(result.refusal_reason, "cloud_permission_required")

    def test_unknown_capability_is_refused(self):
        result = self.registry.select(
            "vendor-special-hat",
            local_engine_available=True,
            fallback_engine_available=True,
            cloud_permission=True,
        )
        self.assertFalse(result.available)
        self.assertEqual(result.refusal_reason, "capability_unavailable")


if __name__ == "__main__":
    unittest.main()
