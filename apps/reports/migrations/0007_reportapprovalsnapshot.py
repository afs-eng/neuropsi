import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0006_specialistrun"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportApprovalSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("payload", models.JSONField(default=dict)),
                ("source_sha256", models.CharField(max_length=64)),
                ("template_name", models.CharField(max_length=255)),
                ("template_sha256", models.CharField(max_length=64)),
                ("document", models.BinaryField()),
                ("document_sha256", models.CharField(max_length=64)),
                ("html", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("report", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="approval_snapshot", to="reports.report")),
            ],
        ),
    ]
