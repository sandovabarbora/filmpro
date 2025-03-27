"""
Logging configuration for the FILMPRO script analysis service.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = "logs"


def configure_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    Path(LOG_DIR).mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("filmpro")
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Prevent duplicate logs
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = RotatingFileHandler(
        f"{LOG_DIR}/filmpro.log", 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    # Set log level for other libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    logger.info("Logging configured")
    return logger