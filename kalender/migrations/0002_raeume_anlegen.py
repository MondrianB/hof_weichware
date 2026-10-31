from django.db import migrations

RAEUME = [
    "Tenne",
    "Scheune",
    "Kaminraum",
    "Modersohn-Raum",
    "Upkammer",
    "Seminarraum 1",
    "Seminarraum 2",
]


def anlegen(apps, schema_editor):
    Raum = apps.get_model("kalender", "Raum")
    for i, name in enumerate(RAEUME, start=1):
        Raum.objects.get_or_create(name=name, defaults={"reihenfolge": i})


def entfernen(apps, schema_editor):
    Raum = apps.get_model("kalender", "Raum")
    Raum.objects.filter(name__in=RAEUME, buchungen__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("kalender", "0001_initial")]
    operations = [migrations.RunPython(anlegen, entfernen)]
