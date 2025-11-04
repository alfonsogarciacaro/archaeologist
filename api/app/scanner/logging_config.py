"""
Logging Configuration for Scanner Service

This module provides comprehensive logging configuration for the RAG system,
including structured logging for long-running tasks and performance monitoring.
"""

import logging
import time
import json
from typing import Dict, Any, Optional
from functools import wraps
from contextlib import asynccontextmanager


class StructuredLogger:
    """
    Structured logger for RAG operations with performance tracking.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_operation_start(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Log the start of an operation"""
        start_time = time.time()
        operation_id = f"{operation}_{int(start_time * 1000)}"
        
        log_data = {
            "event": "operation_started",
            "operation": operation,
            "operation_id": operation_id,
            "start_time": start_time,
            **kwargs
        }
        
        self.logger.info(f"🚀 Starting {operation}: {json.dumps(kwargs, indent=2)}")
        return {"operation_id": operation_id, "start_time": start_time}
    
    def log_operation_end(
        self, 
        operation: str, 
        operation_context: Dict[str, Any], 
        **kwargs
    ) -> None:
        """Log the end of an operation"""
        end_time = time.time()
        duration = end_time - operation_context["start_time"]
        
        log_data = {
            "event": "operation_completed",
            "operation": operation,
            "operation_id": operation_context["operation_id"],
            "end_time": end_time,
            "duration_seconds": duration,
            "duration_ms": int(duration * 1000),
            **kwargs
        }
        
        self.logger.info(
            f"✅ Completed {operation} in {duration:.3f}s ({int(duration * 1000)}ms): "
            f"{json.dumps(kwargs, indent=2)}"
        )
    
    def log_operation_error(
        self, 
        operation: str, 
        operation_context: Dict[str, Any], 
        error: Exception,
        **kwargs
    ) -> None:
        """Log an operation error"""
        end_time = time.time()
        duration = end_time - operation_context["start_time"]
        
        log_data = {
            "event": "operation_failed",
            "operation": operation,
            "operation_id": operation_context["operation_id"],
            "end_time": end_time,
            "duration_seconds": duration,
            "duration_ms": int(duration * 1000),
            "error": str(error),
            "error_type": type(error).__name__,
            **kwargs
        }
        
        self.logger.error(
            f"❌ Failed {operation} after {duration:.3f}s: {str(error)} - "
            f"{json.dumps(kwargs, indent=2)}"
        )
    
    def log_progress(self, operation: str, current: int, total: int, **kwargs) -> None:
        """Log progress for long-running operations"""
        percentage = (current / total) * 100 if total > 0 else 0
        
        log_data = {
            "event": "operation_progress",
            "operation": operation,
            "current": current,
            "total": total,
            "percentage": round(percentage, 2),
            **kwargs
        }
        
        self.logger.info(
            f"📊 {operation} progress: {current}/{total} ({percentage:.1f}%)"
        )
    
    def log_performance_stats(self, operation: str, stats: Dict[str, Any]) -> None:
        """Log performance statistics"""
        self.logger.info(
            f"📈 {operation} performance stats:\n{json.dumps(stats, indent=2)}"
        )


def log_operation(operation_name: str):
    """
    Decorator to automatically log operation start, end, and errors.
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = StructuredLogger(func.__module__)
            
            # Extract meaningful parameters for logging
            log_params = {}
            if args and hasattr(args[0], '__class__'):
                # Log request parameters if this is an endpoint method
                if hasattr(args[1], 'dict'):
                    log_params = {k: v for k, v in args[1].dict().items() 
                               if k not in ['content'] and len(str(v)) < 200}
            
            # Start operation
            operation_context = logger.log_operation_start(operation_name, **log_params)
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Log completion with result stats
                result_stats = {}
                if hasattr(result, 'dict'):
                    result_dict = result.dict()
                    result_stats = {k: v for k, v in result_dict.items() 
                                 if isinstance(v, (int, float, str, list, dict))}
                
                logger.log_operation_end(
                    operation_name, 
                    operation_context, 
                    **result_stats
                )
                
                return result
                
            except Exception as e:
                # Log error
                logger.log_operation_error(
                    operation_name, 
                    operation_context, 
                    e,
                    **log_params
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = StructuredLogger(func.__module__)
            
            # Extract meaningful parameters for logging
            log_params = {}
            if args and hasattr(args[0], '__class__'):
                log_params = {"args_count": len(args), "kwargs_count": len(kwargs)}
            
            # Start operation
            operation_context = logger.log_operation_start(operation_name, **log_params)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log completion
                logger.log_operation_end(operation_name, operation_context)
                
                return result
                
            except Exception as e:
                # Log error
                logger.log_operation_error(operation_name, operation_context, e)
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def log_context(operation: str, logger_name: str = __name__, **kwargs):
    """
    Context manager for logging operations with automatic timing.
    
    Args:
        operation: Name of the operation
        logger_name: Name of the logger
        **kwargs: Additional context to log
    """
    logger = StructuredLogger(logger_name)
    
    # Start operation
    operation_context = logger.log_operation_start(operation, **kwargs)
    
    try:
        yield operation_context
        
        # End operation
        logger.log_operation_end(operation, operation_context)
        
    except Exception as e:
        # Log error
        logger.log_operation_error(operation, operation_context, e)
        raise


def setup_logging(level: str = "INFO") -> None:
    """
    Setup comprehensive logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Setup file handler for detailed logs
    file_handler = logging.FileHandler('scanner_rag.log')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    loggers = [
        'scanner.app.embeddings',
        'scanner.app.text_processing',
        'scanner.app.rag',
        'scanner.app.main'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))