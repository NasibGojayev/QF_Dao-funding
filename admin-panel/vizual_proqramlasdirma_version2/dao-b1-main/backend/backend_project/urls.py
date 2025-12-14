from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

from api import views as api_views
from api import security_middleware as security_views

def root_view(request):
    return JsonResponse({
        'message': 'DAO Quadratic Funding Backend',
        'endpoints': {
            'api': '/api/',
            'public_api': '/api/public/',
            'admin': '/admin/',
            'auth': '/api-token-auth/',
            'stats': '/api/public/stats/',
            'activity': '/api/public/activity/',
            'security': '/api/security/',
            'metrics': '/api/metrics/'
        }
    })

# Authenticated API router
router = routers.DefaultRouter()
router.register(r'projects', api_views.ProjectViewSet)
router.register(r'rounds', api_views.RoundViewSet)
router.register(r'grants', api_views.GrantViewSet)

# Public API router (no auth required)
public_router = routers.DefaultRouter()
public_router.register(r'projects', api_views.PublicProjectViewSet, basename='public-projects')
public_router.register(r'rounds', api_views.PublicRoundViewSet, basename='public-rounds')
public_router.register(r'grants', api_views.PublicGrantViewSet, basename='public-grants')

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/', include(router.urls)),
    path('api/public/', include(public_router.urls)),
    path('api/public/stats/', api_views.dashboard_stats, name='dashboard_stats'),
    path('api/public/activity/', api_views.recent_activity, name='recent_activity'),
    path('api/public/logs/', api_views.system_logs, name='system_logs'),
    
    # Security & Monitoring Endpoints
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


