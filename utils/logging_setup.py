"""
Logging configuration for the application
"""
import logging
import sys
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE

def setup_logging() -> None:
    """
    Configure logging for the application
    """
    # Convert string level to logging level
    level = getattr(logging, LOG_LEVEL)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE)
        ]
    )
    
    # Set levels for external libraries
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)