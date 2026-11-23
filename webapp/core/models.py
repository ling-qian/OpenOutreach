from django.conf import settings
from django.db import models


class Workspace(models.Model):
    name = models.CharField(max_length=160)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="acquisition_workspaces")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ServiceProfile(models.Model):
    workspace = models.OneToOneField(Workspace, on_delete=models.CASCADE, related_name="service_profile")
    service_name = models.CharField(max_length=160, blank=True)
    service_description = models.TextField(blank=True)
    target_industries = models.JSONField(default=list, blank=True)
    target_locations = models.JSONField(default=list, blank=True)
    ideal_customer_description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class Company(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="companies")
    name = models.CharField(max_length=240)
    website = models.URLField(max_length=500, blank=True)
    industry = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=240, blank=True)
    source = models.CharField(max_length=80, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["workspace", "website"], name="uniq_company_website_per_workspace")]


class Evidence(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="evidence")
    category = models.CharField(max_length=80)
    title = models.CharField(max_length=240)
    detail = models.TextField()
    source_url = models.URLField(max_length=1000, blank=True)
    observed_at = models.DateTimeField(auto_now_add=True)
    confidence = models.PositiveSmallIntegerField(default=50)


class Opportunity(models.Model):
    STAGES = [("new", "New"), ("reviewing", "Reviewing"), ("qualified", "Qualified"), ("contacted", "Contacted"), ("won", "Won"), ("dismissed", "Dismissed")]
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="opportunities")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="opportunities")
    score = models.PositiveSmallIntegerField(default=0)
    research_status = models.CharField(max_length=24, default="not_started")
    stage = models.CharField(max_length=24, choices=STAGES, default="new")
    summary = models.TextField(blank=True)
    recommended_service = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OutreachDraft(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="outreach_drafts")
    subject = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=24, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
