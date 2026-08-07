"""The app.* loggers actually write somewhere.

One test, restored after being deleted with the old client's test file. The bug it
guards: nothing configured logging, so every app.* record fell through to
``logging.lastResort``, which drops anything below WARNING. The per-call token-usage
lines are INFO, so across a full day of live runs not one was ever written, while the
code plainly looked like it logged them. ``caplog`` cannot catch this, because
``caplog.at_level`` installs its own handler and bypasses real configuration.
"""

import logging


def test_app_loggers_can_actually_emit_info() -> None:
    import app.main  # noqa: F401  (importing configures the app.* loggers)

    app_logger = logging.getLogger("app")
    assert app_logger.handlers, "app loggers have nowhere to write"
    assert logging.getLogger("app.llm").isEnabledFor(logging.INFO)
