"""Logging utility functions."""
import logging
import json
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from config import config


# Configure the logger
def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with the specified name and level.

    Args:
        name: Name for the logger
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger
    """
    if level is None:
        level_from_config = config.get("log_level", "INFO")
        level = str(level_from_config) if level_from_config else "INFO"

    # Ensure level is a string and not None
    if level is None or not isinstance(level, str):
        level = "INFO"

    # Create logger
    logger = logging.getLogger(name)
    level_value = getattr(logging, level.upper())
    logger.setLevel(level_value)

    # Create console handler and set level
    handler = logging.StreamHandler()
    handler.setLevel(level_value)

    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # Add handler to logger if not already added
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


# Alias for backward compatibility 
get_logger = setup_logger


def format_log_message(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Format a log message with optional context.

    Args:
        message: The log message
        context: Optional dictionary of context information

    Returns:
        Formatted log message
    """
    if not context:
        return message

    # Convert the context to a string
    try:
        context_str = json.dumps(context)
        return f"{message} - Context: {context_str}"
    except (TypeError, ValueError):
        return f"{message} - Context: [Error serializing context]"


def log_exception(
    logger: logging.Logger,
    message: str,
    exception: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an exception with context.

    Args:
        logger: The logger to use
        message: Message describing the error
        exception: The exception that was caught
        context: Optional dictionary of context information
    """
    # Create a dictionary with exception details
    exception_details = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "traceback": traceback.format_exc()
    }

    # Add the current timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    # Combine all context information
    full_context = {
        "timestamp": timestamp,
        "exception": exception_details
    }

    if context:
        full_context.update(context)

    # Log the error
    logger.error(format_log_message(message, full_context))
