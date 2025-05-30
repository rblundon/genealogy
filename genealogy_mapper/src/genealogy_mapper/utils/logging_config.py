import logging
import sys
from pathlib import Path
from rich.logging import RichHandler

def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Set up logging configuration with both file and console handlers.
    
    Args:
        debug (bool): Whether to enable debug logging
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Set up the logger
    logger = logging.getLogger("genealogy_mapper")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler with rich formatting
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=True
    )
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler(
        log_dir / "genealogy_mapper.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    logger.addHandler(file_handler)
    
    return logger 