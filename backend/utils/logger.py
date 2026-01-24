"""
Logging utility for beautiful console output
"""

import logging
import sys
from functools import wraps
import time


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Setup a beautiful logger with colors and formatting
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Custom formatter
    formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger


# Global logger instance
logger = setup_logger()


def timing_decorator(func):
    """
    Decorator to measure execution time of async functions
    
    Usage:
        @timing_decorator
        async def my_function():
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        logger.info(f"⏱️  {func.__name__} completed in {duration:.0f}ms")
        return result
    return wrapper