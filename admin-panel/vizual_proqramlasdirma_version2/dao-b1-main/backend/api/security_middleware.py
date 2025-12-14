"""
Sprint 3: Django Security Middleware and API Integration
Integrates security controls with Django REST Framework
"""

import json
import time
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.conf import settings

# Import security controls
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from security_controls import admin_auth, rate_limiter, data_retention
    from monitoring import kpi_tracker, alert_manager, metrics_collector
except ImportError:
    admin_auth = None
    rate_limiter = None


class SecurityMiddleware:
    """
    Comprehensive security middleware for Django
    - Rate limiting
    - Admin auth for protected endpoints
    - Request/response logging
    - Latency tracking
    """
    
    PROTECTED_PATHS = [
        '/api/',
        '/admin/',
        '/api/public/logs/',
    ]
    
    ADMIN_REQUIRED_PATHS = [
        '/api/admin/',
        '/api/security/',
        '/api/metrics/',
    ]
    
    PUBLIC_PATHS = [
        '/api/public/projects/',
        '/api/public/rounds/',
        '/api/public/grants/',
        '/api/public/stats/',
        '/api/public/activity/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        
        # Rate limiting check
        if rate_limiter and request.path.startswith('/api/'):
            allowed, remaining, reset = rate_limiter.check_rate_limit(client_ip, request.path)
            
            if not allowed:
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'retry_after': reset
                }, status=429)
        
        # Admin auth check for protected endpoints
        if self._requires_admin_auth(request.path):
            auth_result = self._check_admin_auth(request)
            if auth_result:
                return auth_result
        
        # Process request
        response = self.get_response(request)
        
        # Track latency KPI
        latency_ms = (time.time() - start_time) * 1000
        if kpi_tracker:
            kpi_tracker.update_latency(latency_ms)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        if rate_limiter:
            response['X-RateLimit-Remaining'] = str(remaining if 'remaining' in dir() else 100)
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def _requires_admin_auth(self, path):
        return any(path.startswith(p) for p in self.ADMIN_REQUIRED_PATHS)
    
    def _check_admin_auth(self, request):
        if not admin_auth:
            return None
        
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'error': 'Authorization header required',
                'format': 'Bearer <token>'
            }, status=401)
        
        token = auth_header[7:]
        session = admin_auth.validate_session(token)
        
        if not session:
            return JsonResponse({
                'error': 'Invalid or expired token'
            }, status=401)
        
        # Attach session to request for downstream use
        request.admin_session = session
        return None


# ==================== API VIEWS ====================

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["POST"])
def admin_login(request):
    """Admin login endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)
        
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        token = admin_auth.authenticate(username, password, client_ip)
        
        if token:
            return JsonResponse({
                'token': token,
                'message': 'Login successful',
                'expires_in': 28800  # 8 hours
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def admin_logout(request):
    """Admin logout endpoint"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        admin_auth.logout(token, request.META.get('REMOTE_ADDR', 'unknown'))
    
    return JsonResponse({'message': 'Logged out successfully'})


@require_http_methods(["GET"])
def admin_access_logs(request):
    """Get admin access logs"""
    limit = int(request.GET.get('limit', 100))
    logs = admin_auth.get_access_logs(limit)
    return JsonResponse({'logs': logs})


@require_http_methods(["GET"])
def rate_limit_stats(request):
    """Get rate limiting statistics"""
    stats = rate_limiter.get_stats()
    violations = rate_limiter.get_violations(50)
    return JsonResponse({
        'stats': stats,
        'recent_violations': violations
    })


@require_http_methods(["GET"])
def metrics_endpoint(request):
    """Prometheus-compatible metrics endpoint"""
    from security_controls import create_metrics_response
    
    metrics = create_metrics_response(kpi_tracker, alert_manager, rate_limiter)
    return HttpResponse(metrics, content_type='text/plain')


@require_http_methods(["GET"])
def kpi_summary(request):
    """Get KPI summary"""
    summary = kpi_tracker.get_summary()
    return JsonResponse(summary)


@require_http_methods(["GET"])
def alerts_list(request):
    """Get recent alerts"""
    limit = int(request.GET.get('limit', 100))
    alerts = alert_manager.get_recent_alerts(limit)
    return JsonResponse({'alerts': alerts})


@csrf_exempt
@require_http_methods(["POST"])
def simulate_fault(request):
    """Simulate faults for testing alerts"""
    from security_controls import FaultSimulator
    
    try:
        data = json.loads(request.body)
        fault_type = data.get('type')
        
        fault_sim = FaultSimulator(kpi_tracker, alert_manager)
        
        if fault_type == 'event_lag':
            value = data.get('value', 90)
            result = fault_sim.simulate_high_event_lag(value)
        elif fault_type == 'error_rate':
            value = data.get('value', 0.05)
            result = fault_sim.simulate_high_error_rate(value)
        elif fault_type == 'suspicious_transactions':
            value = data.get('value', 60)
            result = fault_sim.simulate_suspicious_transactions(value)
        elif fault_type == 'rate_limit_attack':
            num_requests = data.get('value', 200)
            result = fault_sim.simulate_rate_limit_attack(rate_limiter, num_requests)
        else:
            return JsonResponse({'error': f'Unknown fault type: {fault_type}'}, status=400)
        
        return JsonResponse(result)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@require_http_methods(["GET"])
def security_status(request):
    """Get overall security status"""
    return JsonResponse({
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {
            'admin_auth': admin_auth is not None,
            'rate_limiting': rate_limiter is not None,
            'kpi_tracking': kpi_tracker is not None,
            'alerting': alert_manager is not None
        },
        'kpi_summary': kpi_tracker.get_summary() if kpi_tracker else None,
        'rate_limit_stats': rate_limiter.get_stats() if rate_limiter else None,
        'recent_alerts_count': len(alert_manager.get_recent_alerts(100)) if alert_manager else 0
    })


# URL patterns to add to urls.py
"""
Add these to backend_project/urls.py:

from api import security_middleware as security_views

urlpatterns += [
    path('api/security/login/', security_views.admin_login, name='admin_login'),
    path('api/security/logout/', security_views.admin_logout, name='admin_logout'),
    path('api/security/access-logs/', security_views.admin_access_logs, name='access_logs'),
    path('api/security/status/', security_views.security_status, name='security_status'),
    path('api/metrics/', security_views.metrics_endpoint, name='metrics'),
    path('api/kpis/', security_views.kpi_summary, name='kpi_summary'),
    path('api/alerts/', security_views.alerts_list, name='alerts_list'),
    path('api/rate-limits/', security_views.rate_limit_stats, name='rate_limit_stats'),
    path('api/simulate-fault/', security_views.simulate_fault, name='simulate_fault'),
]
"""
