from django.db import migrations


def add_thcp_instrument(apps, schema_editor):
    instrument = apps.get_model("tests", "Instrument")
    instrument.objects.using(schema_editor.connection.alias).get_or_create(
        code="thcp",
        defaults={
            "name": "THCP - Teste de Habilidades e Conhecimento Pré-Alfabetização",
            "category": "Habilidades pré-alfabetização",
            "version": "1.0",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("tests", "0004_testapplication_status")]
    operations = [migrations.RunPython(add_thcp_instrument, migrations.RunPython.noop)]
