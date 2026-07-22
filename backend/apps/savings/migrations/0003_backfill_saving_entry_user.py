from django.db import migrations


def backfill_user(apps, schema_editor):
    SavingEntry = apps.get_model("savings", "SavingEntry")
    for entry in SavingEntry.objects.filter(user__isnull=True).select_related("trip"):
        entry.user_id = entry.trip.user_id
        entry.save(update_fields=["user"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("savings", "0002_alter_savingentry_unique_together_savingentry_user_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_user, noop),
    ]
