from config.config import LOG_DIR
import logging
from logging.handlers import RotatingFileHandler

import os

from typing import Optional
from fastapi import Request

os.makedirs(f"{LOG_DIR}", exist_ok=True)

# Configure the main logger
log_formatter = logging.Formatter( "%(asctime)s - %(levelname)s - %(module)s - IP: %(message)s")
log_file = f"{LOG_DIR}/server.log"
log_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

# Create main logger instance
logger = logging.getLogger("SecurityCamLogger")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)


# Configure the error logger for logging failures
error_log_file = f"{LOG_DIR}/logger_errors.log"
error_handler = logging.FileHandler(error_log_file)
error_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
error_handler.setLevel(logging.ERROR)

# Create error logger instance
error_logger = logging.getLogger("LoggerErrorHandler")
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)

# Logging function with IP tracking
def log_event( level: str, message: str,request: Optional[Request] = None):
    """
    Logs an event with the specified level and message, including the client's IP address if available.

    Args:
        level (str): The log level (e.g., "info", "warning", "error", "critical").
        message (str): The message to log.
        request (Optional[Request]): The FastAPI request object to extract the client's IP address.

    Raises:
        ValueError: If an invalid log level is provided.
    """
    
    client_ip = request.client.host if request and request.client else "Unknown IP"
    log_message = f"{client_ip} - {message}"
    
    try:
        level = level.lower()
        if level == "info":
            logger.info(log_message)
        elif level == "warning":
            logger.warning(log_message)
        elif level == "error":
            logger.error(log_message)
        elif level == "critical":
            logger.critical(log_message)
        else:
            raise ValueError(f"Invalid log level: {level}")
        
    #     logger.warning(f"Invalid log level '{level}' provided. Defaulting to 'info'.")
    # logger.info(log_message)             AFTER TESTING TO PUT THIS LINE INSTEAD OF THE RAISE TO PREVENT CRASH 
        
    except Exception as e:
        # Log the error to the error logger and fallback to console
        error_logger.error(f"Logging failed: {e}")
        print(f"Logging failed: {e}")