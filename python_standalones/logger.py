import logging
from logging.handlers import RotatingFileHandler

from typing import Optional
from fastapi import Request
# Configure the logger
log_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(module)s - IP: %(message)s"
)

log_file = "logs/server.log"
log_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

# Create logger instance
logger = logging.getLogger("SecurityCamLogger")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# # Console logging
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(log_formatter)
# console_handler.setLevel(logging.INFO)
# logger.addHandler(console_handler)

# Logging function with IP tracking
def log_event( level: str, message: str,request: Optional[Request] = None):
    client_ip = request.client.host if request.client else "Unknown IP"
    log_message = f"{client_ip} - {message}"
    
    if level.lower() == "info":
        logger.info(log_message)
    elif level.lower() == "warning":
        logger.warning(log_message)
    elif level.lower() == "error":
        logger.error(log_message)
    elif level.lower() == "critical":
        logger.critical(log_message)
    else:
        logger.debug(log_message)