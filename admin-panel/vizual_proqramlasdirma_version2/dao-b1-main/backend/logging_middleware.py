"""
Logging Middleware for DAO Backend
Logs all Front-Back and Back-Database data transfers to files
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from functools import wraps
from django.conf import settings

# Create logs directory
LOGS_DIR = Path(settings.BASE_DIR) / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Configure loggers
def setup_logger(name: str, log_file: str, level=logging.INFO):
    """Create a logger with file handler"""
    handler = logging.FileHandler(LOGS_DIR / log_file)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S.%f'
    ))
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

# Create specialized loggers
frontend_logger = setup_logger('frontend', 'frontend_requests.log')
backend_logger = setup_logger('backend', 'backend_api.log')
database_logger = setup_logger('database', 'database_queries.log')


class RequestLoggingMiddleware:
    """
    Middleware to log all incoming requests and outgoing responses
    Captures Front-Back data transfers
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log incoming request
        start_time = datetime.now()
        
        request_data = {
            'timestamp': start_time.isoformat(),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'user': str(request.user) if hasattr(request, 'user') else 'Anonymous'
        }
        
        # Log request body for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = request.body.decode('utf-8')
                if body:
                    request_data['body'] = body[:1000]  # Limit body size
            except:
                pass
        
        frontend_logger.info(f"REQUEST | {json.dumps(request_data)}")
        
        # Get response
        response = self.get_response(request)
        
        # Log response
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        response_data = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration, 2),
            'content_length': len(response.content) if hasattr(response, 'content') else 0
        }
        
        # Log level based on status code
        if response.status_code >= 500:
            backend_logger.error(f"RESPONSE | {json.dumps(response_data)}")
        elif response.status_code >= 400:
            backend_logger.warning(f"RESPONSE | {json.dumps(response_data)}")
        else:
            backend_logger.info(f"RESPONSE | {json.dumps(response_data)}")
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class DatabaseQueryLoggingMiddleware:
    """
    Middleware to log database queries
    Uses Django's connection.queries when DEBUG=True
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.db import connection, reset_queries
        
        reset_queries()
        
        response = self.get_response(request)
        
        # Log queries (only works when DEBUG=True or use django-debug-toolbar)
        if connection.queries:
            for query in connection.queries:
                query_data = {
                    'timestamp': datetime.now().isoformat(),
                    'sql': query.get('sql', '')[:500],  # Limit SQL length
                    'time_ms': float(query.get('time', 0)) * 1000,
                    'path': request.path
                }
                
                # Log slow queries as warnings
                if float(query.get('time', 0)) > 0.1:  # > 100ms
                    database_logger.warning(f"SLOW_QUERY | {json.dumps(query_data)}")
                else:
                    database_logger.debug(f"QUERY | {json.dumps(query_data)}")
        
        return response


def log_database_operation(operation_type: str):
    """
    Decorator to log database operations (INSERT, UPDATE, DELETE)
    Usage: @log_database_operation('INSERT')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                log_data = {
                    'timestamp': datetime.now().isoformat(),
                    'operation': operation_type,
                    'function': func.__name__,
                    'duration_ms': round(duration, 2),
                    'status': 'SUCCESS'
                }
                database_logger.info(f"{operation_type} | {json.dumps(log_data)}")
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                log_data = {
                    'timestamp': datetime.now().isoformat(),
                    'operation': operation_type,
                    'function': func.__name__,
                    'duration_ms': round(duration, 2),
                    'status': 'ERROR',
                    'error': str(e)
                }
                database_logger.error(f"{operation_type} | {json.dumps(log_data)}")
                raise
        
        return wrapper
    return decorator


# API endpoint to retrieve logs
def get_recent_logs(log_type: str = 'all', limit: int = 100):
    """
    Retrieve recent log entries from log files
    """
    logs = []
    
    log_files = {
        'frontend': 'frontend_requests.log',
        'backend': 'backend_api.log',
        'database': 'database_queries.log'
    }
    
    files_to_read = [log_files[log_type]] if log_type in log_files else list(log_files.values())
    
    for filename in files_to_read:
        filepath = LOGS_DIR / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        # Parse log line
                        parts = line.strip().split(' | ', 2)
                        if len(parts) >= 3:
                            logs.append({
                                'timestamp': parts[0],
                                'level': parts[1],
                                'source': filename.replace('.log', '').replace('_', ' ').title(),
                                'message': parts[2]
                            })
                    except:
                        pass
    
    # Sort by timestamp descending
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return logs[:limit]
