from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Count
from .models import Project, Round, Grant
from .serializers import ProjectSerializer, RoundSerializer, GrantSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class RoundViewSet(viewsets.ModelViewSet):
    queryset = Round.objects.all()
    serializer_class = RoundSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class GrantViewSet(viewsets.ModelViewSet):
    queryset = Grant.objects.all()
    serializer_class = GrantSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


# ==================== PUBLIC API (No Auth Required) ====================

class PublicProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to projects for public frontend"""
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]


class PublicRoundViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to rounds for public frontend"""
    queryset = Round.objects.all()
    serializer_class = RoundSerializer
    permission_classes = [AllowAny]


class PublicGrantViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to grants for public frontend"""
    queryset = Grant.objects.all()
    serializer_class = GrantSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_stats(request):
    """Dashboard statistics for frontend"""
    total_projects = Project.objects.count()
    total_rounds = Round.objects.count()
    total_grants = Grant.objects.count()
    total_funding = Grant.objects.aggregate(total=Sum('amount_requested'))['total'] or 0
    
    return Response({
        'total_projects': total_projects,
        'total_rounds': total_rounds,
        'total_grants': total_grants,
        'total_funding': float(total_funding),
        'contributors': 5234,  # Mock - would come from user/donation model
        'active_rounds': Round.objects.count(),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def recent_activity(request):
    """Recent activity for admin dashboard"""
    # Get recent projects
    recent_projects = Project.objects.order_by('-created_at')[:5]
    activities = []
    
    for project in recent_projects:
        activities.append({
            'id': project.id,
            'type': 'Project',
            'description': f'New project submitted: {project.title}',
            'timestamp': project.created_at.isoformat()
        })
    
    # Get recent grants
    recent_grants = Grant.objects.order_by('-created_at')[:5]
    for grant in recent_grants:
        activities.append({
            'id': grant.id,
            'type': 'Contribution',
            'description': f'Grant of ${grant.amount_requested} for {grant.project.title}',
            'timestamp': grant.created_at.isoformat()
        })
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return Response(activities[:10])


@api_view(['GET'])
@permission_classes([AllowAny])
def system_logs(request):
    """System logs endpoint for admin dashboard"""
    import os
    from pathlib import Path
    from django.conf import settings
    
    log_type = request.GET.get('type', 'all')
    limit = int(request.GET.get('limit', 100))
    
    LOGS_DIR = Path(settings.BASE_DIR) / 'logs'
    
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
                source = filename.replace('.log', '').replace('_', ' ').title()
                for line in lines:
                    try:
                        parts = line.strip().split(' | ', 2)
                        if len(parts) >= 3:
                            logs.append({
                                'id': hash(line) % 100000,
                                'timestamp': parts[0],
                                'level': parts[1].lower(),
                                'source': source.split()[0].lower(),
                                'action': parts[2].split(' | ')[0] if ' | ' in parts[2] else 'LOG',
                                'details': parts[2]
                            })
                    except:
                        pass
    
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return Response(logs[:limit])

