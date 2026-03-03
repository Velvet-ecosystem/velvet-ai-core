def test_import_velvet_module():
    from velvet.core.velvet_module import VelvetModule
    assert VelvetModule is not None


def test_import_service():
    import velvet.service  # noqa: F401
