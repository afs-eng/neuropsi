import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('evaluations', '0002_evaluationprogressentry'),
        ('reports', '0009_specialist_provider'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportPreparation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('workflow_version', models.CharField(max_length=50)),
                ('source_sha256', models.CharField(max_length=64)),
                ('manifest', models.JSONField(default=dict)),
                ('blockers', models.JSONField(default=list)),
                ('status', models.CharField(choices=[('prepared', 'Fontes registradas'), ('blocked', 'Pendências identificadas')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_preparations', to='evaluations.evaluation')),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preparations', to='reports.report')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
        migrations.CreateModel(
            name='ReportPreparationStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=50)),
                ('order', models.PositiveSmallIntegerField()),
                ('status', models.CharField(choices=[('completed', 'Concluída'), ('unavailable', 'Não disponível nesta entrega')], max_length=20)),
                ('preparation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='reports.reportpreparation')),
            ],
            options={'ordering': ['order', 'id']},
        ),
        migrations.AddConstraint(
            model_name='reportpreparation',
            constraint=models.UniqueConstraint(fields=('report', 'workflow_version', 'source_sha256'), name='unique_report_preparation_source'),
        ),
        migrations.AddConstraint(
            model_name='reportpreparationstep',
            constraint=models.UniqueConstraint(fields=('preparation', 'key'), name='unique_preparation_step'),
        ),
    ]
