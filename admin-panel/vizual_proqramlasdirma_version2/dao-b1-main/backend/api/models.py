from django.db import models
from django.conf import settings


class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata_uri = models.CharField(max_length=1024, blank=True)

    def __str__(self):
        return self.title


class Round(models.Model):
    name = models.CharField(max_length=200)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    def __str__(self):
        return self.name


class Grant(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    amount_requested = models.DecimalField(max_digits=20, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Grant for {self.project.title}"
