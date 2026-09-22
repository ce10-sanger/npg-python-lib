import logging

import pytest
import structlog


@pytest.fixture()
def reset_logging():
    """
    Resets logging before and after each test to isolate a test from pytest
    logging plugin and other tests.

    Logging has global state which is modified by pytest logging plugin and
    may be modified by a test.

    logging.basicConfig does nothing if root logger already has handlers configured.

    Disables caplog functionality.
    """

    # Remove pytest logging plugin
    root = logging.getLogger()
    pytest_handlers = root.handlers[:]
    original_level = root.level

    root.handlers.clear()
    structlog.reset_defaults()

    yield

    # Remove
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        if handler not in pytest_handlers:
            handler.close()

    # Restore pytest logging plugin
    root.handlers[:] = pytest_handlers
    root.setLevel(original_level)
    structlog.reset_defaults()
