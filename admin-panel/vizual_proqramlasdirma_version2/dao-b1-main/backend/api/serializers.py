from rest_framework import serializers
from .models import Project, Round, Grant


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'owner', 'created_at', 'metadata_uri']


class RoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = ['id', 'name', 'start_at', 'end_at']


class GrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grant
        fields = ['id', 'project', 'amount_requested', 'created_at']
