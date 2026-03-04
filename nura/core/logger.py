import sys
from datetime import datetime

from loguru import logger as _logger

_print_level = "INFO"

_context_log_file = None

_logger_initialized = False


def _ensure_logger_initialized():
    """Lazy initialization of logger to avoid circular imports."""
    global _logger_initialized
    if not _logger_initialized:
        from nura.core.config import PROJECT_ROOT

        current_date = datetime.now()
        formatted_date = current_date.strftime("%Y%m%d%H%M%S")

        _logger.remove()
        _logger.add(sys.stderr, level="INFO")
        _logger.add(PROJECT_ROOT / f"logs/{formatted_date}.log", level="DEBUG")
        _logger_initialized = True


class LoggerProxy:
    """Proxy class for lazy initialization of logger."""

    def __getattr__(self, name):
        _ensure_logger_initialized()
        return getattr(_logger, name)

    def __call__(self, *args, **kwargs):
        _ensure_logger_initialized()
        return _logger(*args, **kwargs)


logger = LoggerProxy()


def get_context_logger():
    """Get a file handle for writing complete context logs.

    This writes directly to a file without going through loguru,
    avoiding duplicate output issues.
    """
    from nura.core.config import PROJECT_ROOT

    global _context_log_file
    if _context_log_file is None:
        current_date = datetime.now()
        formatted_date = current_date.strftime("%Y%m%d%H%M%S")
        log_path = PROJECT_ROOT / f"logs/context_{formatted_date}.log"
        _context_log_file = open(log_path, "w", encoding="utf-8")
    return _context_log_file


def close_context_logger():
    """Close the context log file."""
    global _context_log_file
    if _context_log_file is not None:
        _context_log_file.close()
        _context_log_file = None


def context_log(message: str):
    """Write a message to the context log file."""
    f = get_context_logger()
    f.write(message + "\n")
    f.flush()


if __name__ == "__main__":
    logger.info("Starting application")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
