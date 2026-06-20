from velvet.core.authority import AuthorityContext, Court, Intent


def test_court_allows_scoped_action():
    intent = Intent(action="read_status", actor="velvet", target="vehicle")
    context = AuthorityContext(
        allowed_actions=frozenset({"read_status"}),
        allowed_targets=frozenset({"vehicle"}),
    )

    receipt = Court().evaluate(intent, context)

    assert receipt.authorized is True
    assert receipt.reason == "authorized by Court"


def test_court_denies_unlisted_action():
    intent = Intent(action="write_setting", actor="client", target="vehicle")
    context = AuthorityContext(
        allowed_actions=frozenset({"read_status"}),
        allowed_targets=frozenset({"vehicle"}),
    )

    receipt = Court().evaluate(intent, context)

    assert receipt.authorized is False
    assert receipt.reason == "action is not allowed"


def test_court_requires_presence_for_elevated_request():
    intent = Intent(
        action="maintenance_mode",
        actor="owner",
        target="core",
        privilege_elevation=True,
    )
    context = AuthorityContext(
        presence_verified=False,
        allowed_actions=frozenset({"maintenance_mode"}),
        allowed_targets=frozenset({"core"}),
    )

    receipt = Court().evaluate(intent, context)

    assert receipt.authorized is False
    assert receipt.reason == "verified physical presence is required"
