
"""
Logging Configuration
Sets up structured logging for the application
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def setup_logger(config: Dict[str, Any], name: Optional[str] = None) -> logging.Logger:
    """Set up structured logging with configuration"""
    
    # Get logger
    logger_name = name or 'contentdm_ai'
    logger = logging.getLogger(logger_name)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set level
    level = getattr(logging, config.get('level', 'INFO').upper())
    logger.setLevel(level)
    
    # Create formatter
    log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = config.get('file', 'contentdm_ai.log')
    if log_file:
        try:
            # Create logs directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance by name"""
    return logging.getLogger(name)

class StreamlitLogHandler(logging.Handler):
    """Custom log handler for Streamlit applications"""
    
    def __init__(self, streamlit_container=None):
        super().__init__()
        self.container = streamlit_container
        self.logs = []
    
    def emit(self, record):
        """Emit a log record"""
        try:
            msg = self.format(record)
            self.logs.append({
                'timestamp': record.created,
                'level': record.levelname,
                'message': msg,
                'logger': record.name
            })
            
            # Keep only last 100 logs
            if len(self.logs) > 100:
                self.logs = self.logs[-100:]
                
        except Exception:
            self.handleError(record)
    
    def get_logs(self):
        """Get stored log messages"""
        return self.logs
    
    def clear_logs(self):
        """Clear stored log messages"""
        self.logs.clear()

def setup_streamlit_logging(config: Dict[str, Any]) -> StreamlitLogHandler:
    """Set up logging for Streamlit application"""
    
    # Create custom handler
    streamlit_handler = StreamlitLogHandler()
    
    # Set up formatter
    log_format = config.get('format', '%(asctime)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter(log_format)
    streamlit_handler.setFormatter(formatter)
    
    # Set level
    level = getattr(logging, config.get('level', 'INFO').upper())
    streamlit_handler.setLevel(level)
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(streamlit_handler)
    root_logger.setLevel(level)
    
    # Also set up file logging
    setup_logger(config)
    
    return streamlit_handler

def configure_external_loggers():
    """Configure external library loggers"""
    
    # Reduce noise from external libraries
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

class ContextFilter(logging.Filter):
    """Add context information to log records"""
    
    def __init__(self, context: Dict[str, Any]):
        super().__init__()
        self.context = context
    
    def filter(self, record):
        """Add context to log record"""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True

def add_context_to_logger(logger: logging.Logger, context: Dict[str, Any]):
    """Add context information to logger"""
    context_filter = ContextFilter(context)
    logger.addFilter(context_filter)

def create_performance_logger(name: str) -> logging.Logger:
    """Create a performance-focused logger"""
    logger = logging.getLogger(f"{name}_performance")
    
    # Only log to file for performance tracking
    handler = logging.FileHandler(f"{name}_performance.log")
    formatter = logging.Formatter(
        '%(asctime)s,%(name)s,%(funcName)s,%(lineno)d,%(levelname)s,%(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    return logger
