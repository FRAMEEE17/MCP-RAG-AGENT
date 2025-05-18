import logging
import sys
from .config import config

def setup_logger(name: str = "rag-mcp") -> logging.Logger:
    """Set up and return a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.logging.level))
    
    # Create console handler 
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Create a global logger instance
logger = setup_logger()