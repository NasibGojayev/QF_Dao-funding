import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin

# Use the 'api' logger configured in settings.py
logger = logging.getLogger("api")


class LogEverythingMiddleware(MiddlewareMixin):
    """
    Comprehensive request/response logging middleware.
    Logs all HTTP requests with timing, headers, and response details.
    """
    
    def process_request(self, request):
        """Called before view - start timing and log request details"""
        request._start_time = time.time()
        
        # Build request log data
        log_data = {
            "type": "REQUEST",
            "method": request.method,
            "path": request.path,
            "query_params": dict(request.GET),
            "user": str(request.user) if hasattr(request, 'user') else "Anonymous",
            "ip": self.get_client_ip(request),
            "user_agent": request.META.get('HTTP_USER_AGENT', '')[:100],
        }
        
        # Log request body for POST/PUT/PATCH (truncated)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = request.body.decode('utf-8')[:500]
                # Try to parse as JSON for cleaner logging
                if request.content_type == 'application/json' and body:
                    log_data["body_preview"] = json.loads(body)
                else:
                    log_data["body_preview"] = body
            except Exception:
                log_data["body_preview"] = "[Unable to decode body]"
        
        logger.info(f"→ {request.method} {request.path} | {json.dumps(log_data)}")
        return None
    
    def process_response(self, request, response):
        """Called after view - log response details and timing"""
        # Calculate response time
        start_time = getattr(request, '_start_time', None)
        duration_ms = (time.time() - start_time) * 1000 if start_time else 0
        
        log_data = {
            "type": "RESPONSE",
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "content_length": len(response.content) if hasattr(response, 'content') else 0,
        }
        
        # Log level based on status code
        if response.status_code >= 500:
            logger.error(f"← {response.status_code} {request.path} ({duration_ms:.2f}ms) | {json.dumps(log_data)}")
        elif response.status_code >= 400:
            logger.warning(f"← {response.status_code} {request.path} ({duration_ms:.2f}ms) | {json.dumps(log_data)}")
        else:
            logger.info(f"← {response.status_code} {request.path} ({duration_ms:.2f}ms) | {json.dumps(log_data)}")
        
        return response
    
    def get_client_ip(self, request):
        """Extract client IP from request headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
