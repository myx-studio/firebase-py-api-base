"""Logging middleware for Firebase Functions."""
from typing import Any, Callable
import json
import logging
import time
from functools import wraps
from config import config
from flask import Response, request

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get("log_level", "INFO")),
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("api")


def log_request(req: Any = None) -> None:
    """
    Log details about an incoming request.

    Args:
        req: The HTTP request object (optional, will use Flask request object if None)
    """
    # Use the global request object if no request is provided
    req = req or request

    # Extract basic request info
    method = req.method
    path = req.path
    query_params = dict(req.args)
    headers = {k: v for k, v in req.headers.items()
                if k.lower() not in ["authorization", "cookie"]}

    # Don't log request body for security reasons (might contain sensitive data)
    # But you can log the content type and length
    content_type = req.headers.get("Content-Type", "")
    content_length = req.headers.get("Content-Length", "0")

    # Create log entry
    log_data = {
        "method": method,
        "path": path,
        "query_params": query_params,
        "headers": headers,
        "content_type": content_type,
        "content_length": content_length,
        "remote_addr": req.headers.get("X-Forwarded-For", "unknown")
    }

    logger.info("Request received: %s", json.dumps(log_data))


def request_logger(func: Callable) -> Callable:
    """
    Decorator to log requests and responses with timing information.

    Args:
        func: The function to decorate

    Returns:
        Decorated function that logs request/response info
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        # Log the request
        log_request()

        # Record start time
        start_time = time.time()

        try:
            # Execute the original function
            response = func(*args, **kwargs)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Log the response
            logger.info(
                "Response sent: status=%d, execution_time=%.4fs",
                response.status_code, execution_time
            )

            return response
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time

            # Log the error
            logger.error(
                "Error during request processing: %s, execution_time=%.4fs",
                str(e), execution_time
            )

            # Re-raise the exception
            raise

    return wrapper
