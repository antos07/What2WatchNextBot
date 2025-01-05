import functools
import inspect
import logging
import sys
import time
import typing

from loguru import logger

type LogLevel = typing.Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def configure(level: LogLevel = "INFO"):
    # Setup interception of logs from the standard logging library.
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    logger.remove()
    logger.add(sys.stderr, level=level, format=_format)


def _format(record):
    format_ = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
        " | "
        "<level>{level: <8}</level>"
        " | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        " | "
        "<level>{message}</level>"
    )
    if record["extra"]:
        format_ += " | <level>{extra}</level>"
    format_ += "\n"
    return format_


# Taken from loguru docs
def logger_wraps(*, entry=True, exit=True, level="DEBUG"):
    def wrapper(func):
        name = func.__qualname__

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapped(*args, **kwargs):
                logger_ = logger.opt(depth=1)
                if entry:
                    logger_.log(
                        level, "Entering '{}' (args={}, kwargs={})", name, args, kwargs
                    )
                start_s = time.time()
                result = await func(*args, **kwargs)
                end_s = time.time()
                execution_time_ms = (end_s - start_s) * 1000
                if exit:
                    logger_.log(
                        level,
                        "Exiting '{}' in {:.0f} ms (result={})",
                        name,
                        execution_time_ms,
                        result,
                    )
                return result
        else:

            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                logger_ = logger.opt(depth=1)
                if entry:
                    logger_.log(
                        level, "Entering '{}' (args={}, kwargs={})", name, args, kwargs
                    )
                start = time.time()
                result = func(*args, **kwargs)
                end = time.time()
                if exit:
                    logger_.log(
                        level,
                        "Exiting '{}' in {:.2f} s (result={})",
                        name,
                        end - start,
                        result,
                    )
                return result

        return wrapped

    return wrapper


# The following class taken from loguru's docs. It implements
# a handler for standard logging module that redirects all
# the logs to loguru.
class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
