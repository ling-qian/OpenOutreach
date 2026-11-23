from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("acquisition_web", "0001_initial")]
    operations = [
        migrations.AddField(model_name="company", name="prospect_contacts", field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name="company", name="icp_verdict", field=models.CharField(blank=True, max_length=24)),
        migrations.AddField(model_name="company", name="icp_reason", field=models.TextField(blank=True)),
        migrations.AddField(model_name="company", name="discovery_source_url", field=models.URLField(blank=True, max_length=1000)),
        migrations.AddField(model_name="opportunity", name="brief_data", field=models.JSONField(blank=True, default=dict)),
    ]
