# Generated by Django 5.0.6 on 2025-01-17 16:54

from django.conf import settings
from django.db import migrations, models


def add_funder_note_content_type(apps, schema_editor):
    FunderNote = apps.get_model("ukgrantmaking", "FunderNote")
    ContentType = apps.get_model("contenttypes", "ContentType")
    for note in FunderNote.objects.all():
        note.content_type = ContentType.objects.get_for_model(note.funder)
        note.object_id = note.funder.org_id
        note.save()


def reverse_add_funder_note_content_type(apps, schema_editor):
    FunderNote = apps.get_model("ukgrantmaking", "FunderNote")
    for note in FunderNote.objects.all():
        note.funder = note.content_object
        note.save()


def copy_notes_from_funder_year(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    FunderYear = apps.get_model("ukgrantmaking", "FunderYear")
    FunderNote = apps.get_model("ukgrantmaking", "FunderNote")

    funder_year_content_type = ContentType.objects.get_for_model(FunderYear)

    for funder_year in FunderYear.objects.exclude(
        models.Q(notes__isnull=True) | models.Q(notes__exact="")
    ).select_related("funder_financial_year"):
        FunderNote.objects.create(
            content_type=funder_year_content_type,
            object_id=funder_year.id,
            funder=funder_year.funder_financial_year.funder,
            note=funder_year.notes,
            date_added=funder_year.checked_on,
            date_updated=funder_year.checked_on,
            added_by=funder_year.funder_financial_year.checked_by,
        )
        if funder_year.funder_financial_year.notes and (
            funder_year.funder_financial_year.notes != funder_year.notes
        ):
            FunderNote.objects.create(
                content_type=funder_year_content_type,
                object_id=funder_year.id,
                funder=funder_year.funder_financial_year.funder,
                note=funder_year.funder_financial_year.notes,
                date_added=funder_year.funder_financial_year.checked_on,
                date_updated=funder_year.funder_financial_year.checked_on,
                added_by=funder_year.funder_financial_year.checked_by,
            )


def reverse_copy_notes_from_funder_year(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    FunderYear = apps.get_model("ukgrantmaking", "FunderYear")
    FunderNote = apps.get_model("ukgrantmaking", "FunderNote")

    funder_year_content_type = ContentType.objects.get_for_model(FunderYear)

    for note in FunderNote.objects.filter(content_type=funder_year_content_type):
        note.content_object.notes += note.note
        note.content_object.save()
        note.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("ukgrantmaking", "0102_remove_funderfinancialyear_notes_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(
            add_funder_note_content_type, reverse_add_funder_note_content_type
        ),
        migrations.RunPython(
            copy_notes_from_funder_year, reverse_copy_notes_from_funder_year
        ),
    ]
