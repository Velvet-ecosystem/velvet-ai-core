from velvet.core.authority import Dispatcher, Intent, IntentHandler, Receipt


class StatusHandler(IntentHandler):
    name = "status_handler"

    def handle(self, intent: Intent):
        return {"status": "ok", "target": intent.target}


def test_dispatcher_rejects_denied_receipt():
    intent = Intent(action="read_status", actor="velvet", target="vehicle")
    decision = Receipt.create(
        intent_action=intent.action,
        actor=intent.actor,
        target=intent.target,
        authorized=False,
        reason="denied by Court",
    )

    receipt = Dispatcher().dispatch(intent, decision)

    assert receipt.authorized is False
    assert receipt.reason == "dispatch denied: Court did not authorize intent"


def test_dispatcher_routes_authorized_intent():
    intent = Intent(action="read_status", actor="velvet", target="vehicle")
    decision = Receipt.create(
        intent_action=intent.action,
        actor=intent.actor,
        target=intent.target,
        authorized=True,
        reason="authorized by Court",
    )
    dispatcher = Dispatcher()
    dispatcher.register("vehicle", StatusHandler())

    receipt = dispatcher.dispatch(intent, decision)

    assert receipt.authorized is True
    assert receipt.executor == "status_handler"
    assert "status" in receipt.outcome
