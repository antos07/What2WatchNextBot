"""Logging configuration and initialization."""

import inspect
import logging
import sys
import typing

import loguru
import pydantic_settings
from loguru import logger

__all__ = ["Config", "init", "logger"]

type LogLevel = typing.Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Config(pydantic_settings.BaseSettings, env_prefix="LOG_"):
    """Logging configuration.

    :ivar level: Logging level. Defaults to ``"INFO"``.
    :ivar diagnose: Enable diagnose mode (shows detailed tracebacks).
        Defaults to ``False``.
    """

    level: LogLevel = "INFO"
    diagnose: bool = False


# The following class taken from loguru's docs. It implements
# a handler for the standard logging module that redirects all
# the logs to loguru.
class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get the corresponding Loguru level if it exists.
        level: str | int
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        loguru.logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def init(config: Config) -> None:
    """Initialize and configure logging.

    **IMPORTANT**: This will delete all existing handlers!.

    :param config: Logging configuration.
    """

    # Setup interception of logs from the standard logging library.
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # Setup loguru
    loguru.logger.remove()
    loguru.logger.add(
        sink=sys.stderr,
        level=config.level,
        diagnose=config.diagnose,
    )
