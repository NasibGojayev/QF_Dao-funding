"""
Django Middleware for Security Logging
Add this to Django's MIDDLEWARE setting to capture real request data
"""
import json
import time
from datetime import datetime
from pathlib import Path

# Log file path - shared with security dashboard
SECURITY_LOGS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "security" / "logs"


class SecurityLoggingMiddleware:
    """
    Middleware to log all Django requests to a file that the security dashboard can read.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        SECURITY_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    def __call__(self, request):
        # Record start time
        start_time = time.time()
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        # Process request
        response = self.get_response(request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Get user
        user = str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
        
        # Log the request
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "ip": ip,
            "user": user,
            "response_time_ms": round(response_time_ms, 2),
            "user_agent": request.META.get('HTTP_USER_AGENT', '')[:200]
        }
        
        # Write to log file
        log_file = SECURITY_LOGS_DIR / "django_requests.jsonl"
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            pass  # Don't break the request if logging fails
        
        # Also log connections for geo tracking
        if ip and ip not in ('127.0.0.1', 'localhost'):
            conn_file = SECURITY_LOGS_DIR / "connections.jsonl"
            try:
                conn_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "ip": ip,
                    "endpoint": request.path,
                    "user_agent": request.META.get('HTTP_USER_AGENT', '')[:200],
                    "user": user,
                    "status": "success" if response.status_code < 400 else "error"
                }
                with open(conn_file, 'a') as f:
                    f.write(json.dumps(conn_entry) + "\n")
            except:
                pass
        
        return response


class SecurityEventMiddleware:
    """
    Middleware to log security-relevant events (auth, admin, errors)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        SECURITY_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log security-relevant events
        category = None
        action = None
        outcome = "success"
        
        # Authentication events
        if '/auth/' in request.path or '/login' in request.path or '/token' in request.path:
            category = "authentication"
            action = f"{request.method} {request.path}"
            outcome = "success" if response.status_code < 400 else "failure"
        
        # Admin events
        elif '/admin/' in request.path:
            category = "admin_action"
            action = f"{request.method} {request.path}"
            outcome = "success" if response.status_code < 400 else "failure"
        
        # Error events
        elif response.status_code >= 400:
            category = "api_error"
            action = f"{request.method} {request.path} -> {response.status_code}"
            outcome = "failure"
        
        # Log if relevant
        if category:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR', '')
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "action": action,
                "source_ip": ip,
                "user": str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
                "outcome": outcome,
                "details": {"status_code": response.status_code}
            }
            
            log_file = SECURITY_LOGS_DIR / "siem_events.jsonl"
            try:
                with open(log_file, 'a') as f:
                    f.write(json.dumps(event) + "\n")
            except:
                pass
        
        return response
