"""Core decisions are descriptive; they cannot invoke an executor callback."""

import unittest
from unittest.mock import Mock

from velvet.core.authority import AuthorityContext, Court, Dispatcher, Intent, IntentHandler, Receipt


class StatusHandler(IntentHandler):
    name = "status_handler"

    def __init__(self):
        self.calls = []

    def handle(self, intent):
        self.calls.append(intent)
        return {"status": "ok"}


class DispatcherBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.intent = Intent("read_status", "guest", "telemetry", {"detail": "summary"})
        self.decision = Court().evaluate(
            self.intent,
            AuthorityContext(allowed_actions=frozenset({"read_status"}),
                             allowed_targets=frozenset({"telemetry"})),
        )

    def test_callback_registration_is_retired(self):
        handler = StatusHandler()
        with self.assertRaisesRegex(RuntimeError, "Runtime"):
            Dispatcher().register("telemetry", handler)
        self.assertEqual(handler.calls, [])

    def test_old_or_forged_registry_cannot_restore_dispatch(self):
        dispatcher = Dispatcher()
        handler = StatusHandler()
        # Simulate a legacy object or an injected registry; dispatch must never use it.
        dispatcher._handlers = {"telemetry": handler, "forbidden": handler}
        variants = [
            self.intent,
            Intent("write_setting", "guest", "telemetry"),
            Intent("read_status", "other-actor", "telemetry"),
            Intent("read_status", "guest", "forbidden"),
            Intent("read_status", "guest", "telemetry", {"detail": "changed"}),
        ]
        for intent in variants:
            with self.subTest(intent=intent):
                with self.assertRaisesRegex(RuntimeError, "Runtime"):
                    dispatcher.dispatch(intent, self.decision)
        self.assertEqual(handler.calls, [])

    def test_approval_truth_signature_expiry_and_simulation_claims_cannot_enable_dispatch(self):
        forged = Mock()
        forged.authorized = True
        denied = Receipt.create(intent_action="read_status", actor="guest", target="telemetry",
                                authorized=False, reason="denied")
        for decision in (self.decision, denied, forged, True, None,
                         {"authorized": True, "simulation_only": True, "expires_at": 9999999999}):
            with self.subTest(decision=decision):
                dispatcher = Dispatcher()
                handler = Mock()
                dispatcher._handlers = {"telemetry": handler}
                for _ in range(2):
                    with self.assertRaisesRegex(RuntimeError, "Runtime"):
                        dispatcher.dispatch(self.intent, decision)
                handler.handle.assert_not_called()
        self.assertEqual(forged.mock_calls, [])

    def test_educational_court_evaluation_remains_available(self):
        self.assertTrue(self.decision.authorized)
        self.assertIsNone(self.decision.executor)
        self.assertIsNone(self.decision.outcome)
        denied = Court().evaluate(Intent("write", "guest", "vehicle"), AuthorityContext())
        self.assertFalse(denied.authorized)


if __name__ == "__main__":
    unittest.main()
