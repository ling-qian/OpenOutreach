from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("openoutreach_config", "0004_remove_siteconfig_apollo_and_email_finder"),
    ]
    operations = [
        migrations.CreateModel(
            name="Workspace",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="acquisition_workspaces", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=240)),
                ("website", models.URLField(blank=True, max_length=500)),
                ("industry", models.CharField(blank=True, max_length=160)),
                ("location", models.CharField(blank=True, max_length=240)),
                ("source", models.CharField(default="manual", max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="companies", to="acquisition_web.workspace")),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="Evidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(max_length=80)),
                ("title", models.CharField(max_length=240)),
                ("detail", models.TextField()),
                ("source_url", models.URLField(blank=True, max_length=1000)),
                ("observed_at", models.DateTimeField(auto_now_add=True)),
                ("confidence", models.PositiveSmallIntegerField(default=50)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence", to="acquisition_web.company")),
            ],
        ),
        migrations.CreateModel(
            name="Opportunity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.PositiveSmallIntegerField(default=0)),
                ("research_status", models.CharField(default="not_started", max_length=24)),
                ("stage", models.CharField(choices=[("new", "New"), ("reviewing", "Reviewing"), ("qualified", "Qualified"), ("contacted", "Contacted"), ("won", "Won"), ("dismissed", "Dismissed")], default="new", max_length=24)),
                ("summary", models.TextField(blank=True)),
                ("recommended_service", models.CharField(blank=True, max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="opportunities", to="acquisition_web.company")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="opportunities", to="acquisition_web.workspace")),
            ],
        ),
        migrations.CreateModel(
            name="OutreachDraft",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(blank=True, max_length=300)),
                ("body", models.TextField()),
                ("status", models.CharField(default="draft", max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("opportunity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outreach_drafts", to="acquisition_web.opportunity")),
            ],
        ),
        migrations.CreateModel(
            name="ServiceProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("service_name", models.CharField(blank=True, max_length=160)),
                ("service_description", models.TextField(blank=True)),
                ("target_industries", models.JSONField(blank=True, default=list)),
                ("target_locations", models.JSONField(blank=True, default=list)),
                ("ideal_customer_description", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("workspace", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="service_profile", to="acquisition_web.workspace")),
            ],
        ),
    ]
