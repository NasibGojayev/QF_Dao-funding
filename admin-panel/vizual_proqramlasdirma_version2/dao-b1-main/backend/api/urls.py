from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'rounds', views.RoundViewSet)
router.register(r'grants', views.GrantViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
