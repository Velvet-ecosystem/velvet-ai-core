import importlib.util
from pathlib import Path
import unittest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate_promotion_evidence.py"
)
spec = importlib.util.spec_from_file_location("promotion_evidence", str(SCRIPT))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PromotionEvidenceTests(unittest.TestCase):
    def test_failed_status_is_normalized_and_authority_stays_false(self):
        evidence = module.build_evidence(
            repository="repo",
            module_id="module",
            suite="tests",
            status="1",
            python_version="3.10",
            environment={"GITHUB_SHA": "abc"},
        )
        self.assertEqual(evidence["status"], "failed")
        self.assertEqual(evidence["commit_sha"], "abc")
        self.assertFalse(
            evidence["architecture_assertions"][
                "authority_granted_by_evidence"
            ]
        )
        self.assertFalse(
            evidence["architecture_assertions"][
                "simulated_input_may_unlock_physical_target"
            ]
        )


if __name__ == "__main__":
    unittest.main()
