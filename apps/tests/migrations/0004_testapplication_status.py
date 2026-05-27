from django.db import migrations, models


def populate_status(apps, schema_editor):
    TestApplication = apps.get_model("tests", "TestApplication")
    for application in TestApplication.objects.all().iterator():
        if application.is_validated:
            status = "reviewed"
        elif (application.interpretation_text or "").strip():
            status = "interpreted"
        elif application.classified_payload or application.computed_payload:
            status = "scored"
        elif application.raw_payload or application.reviewed_payload or application.applied_on:
            status = "completed"
        else:
            status = "draft"
        TestApplication.objects.filter(id=application.id).update(status=status)


class Migration(migrations.Migration):

    dependencies = [
        ("tests", "0003_add_wais3_instrument"),
    ]

    operations = [
        migrations.AddField(
            model_name="testapplication",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Rascunho"),
                    ("completed", "Aplicação concluída"),
                    ("scored", "Corrigido"),
                    ("interpreted", "Interpretação gerada"),
                    ("reviewed", "Revisado"),
                    ("locked", "Travado"),
                ],
                default="draft",
                max_length=20,
                verbose_name="status",
            ),
        ),
        migrations.RunPython(populate_status, migrations.RunPython.noop),
    ]
