import logging
import os
from datetime import datetime

def get_security_logger():
    """
    Configures and returns a logger for security events.
    The log file is located at backend/security_logs/security.log.
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'security_logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'security.log')

    logger = logging.getLogger('security_logger')
    logger.setLevel(logging.INFO)

    # Check if handler already exists to avoid duplicate logs
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def log_security_event(message, level='info'):
    """
    Logs a security event with the specified message and level.
    """
    logger = get_security_logger()
    if level.lower() == 'info':
        logger.info(message)
    elif level.lower() == 'warning':
        logger.warning(message)
    elif level.lower() == 'error':
        logger.error(message)
    elif level.lower() == 'critical':
        logger.critical(message)
    else:
        logger.info(message)
