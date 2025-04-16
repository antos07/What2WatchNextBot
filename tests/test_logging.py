import io
import logging
import sys
from collections.abc import Generator

import loguru
import pytest

import app.logging


@pytest.fixture(autouse=True)
def reset_logging() -> Generator[None, None, None]:
    yield

    # Reset logging configuration after each test
    logging.basicConfig(force=True)
    loguru.logger.remove()
    loguru.logger.add(sys.stderr)


class TestInit:
    def test_default_level_is_info(self, monkeypatch: pytest.MonkeyPatch):
        output_file = io.StringIO()
        monkeypatch.setattr(sys, "stderr", output_file)

        app.logging.init(app.logging.Config())

        app.logging.logger.info("This should be printed")
        app.logging.logger.debug("This should not be printed")

        assert "This should be printed" in output_file.getvalue()
        assert "This should not be printed" not in output_file.getvalue()

    def test_default_diagnose_is_false(self, monkeypatch: pytest.MonkeyPatch):
        output_file = io.StringIO()
        monkeypatch.setattr(sys, "stderr", output_file)

        app.logging.init(app.logging.Config())

        def raise_error(secret_parameter):
            raise ValueError("Error")

        secret_message = "This should not be logged"
        try:
            raise_error(secret_message)
        except ValueError:
            app.logging.logger.exception("Checking...")

        assert secret_message not in output_file.getvalue()

    def test_when_diagnose_is_true(self, monkeypatch: pytest.MonkeyPatch):
        output_file = io.StringIO()
        monkeypatch.setattr(sys, "stderr", output_file)

        app.logging.init(app.logging.Config(diagnose=True))

        def raise_error(secret_parameter):
            raise ValueError("Error")

        secret_message = "This should be logged"
        try:
            raise_error(secret_message)
        except ValueError:
            app.logging.logger.exception("Checking...")

        assert secret_message in output_file.getvalue()

    def test_standard_logging_is_redirected(self, monkeypatch: pytest.MonkeyPatch):
        output_file = io.StringIO()
        monkeypatch.setattr(sys, "stderr", output_file)

        app.logging.init(app.logging.Config())

        logging.info("This should be printed")

        assert "This should be printed" in output_file.getvalue()
