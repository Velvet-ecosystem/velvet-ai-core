# SPDX-License-Identifier: GPL-3.0-only

import inspect
import unittest

from velvet_ai_core.brain_adapter import BrainAdapter


class TestBrainAdapterCompatibility(unittest.TestCase):
    def test_constructs_without_arguments(self):
        adapter = BrainAdapter()
        self.assertIsInstance(adapter, BrainAdapter)

    def test_rejects_positional_runtime_references(self):
        with self.assertRaises(TypeError):
            BrainAdapter(object())

    def test_rejects_keyword_runtime_references(self):
        with self.assertRaises(TypeError):
            BrainAdapter(bus=object())

    def test_has_no_instance_dictionary(self):
        adapter = BrainAdapter()
        self.assertFalse(hasattr(adapter, "__dict__"))

    def test_exposes_no_attach_method(self):
        adapter = BrainAdapter()
        self.assertFalse(hasattr(adapter, "attach"))

    def test_constructor_contract_is_empty(self):
        signature = inspect.signature(BrainAdapter)
        self.assertEqual(tuple(signature.parameters), ())


if __name__ == "__main__":
    unittest.main()
