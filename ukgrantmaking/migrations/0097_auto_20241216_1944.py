# Generated by Django 5.0.6 on 2024-12-16 19:44

from django.db import migrations


def update_funder_financial_year(apps, schema_editor):
    FunderYear = apps.get_model("ukgrantmaking", "FunderYear")
    for funder_year in FunderYear.objects.filter(
        original_funder_financial_year__isnull=False
    ).exclude(original_funder_financial_year_id=0):
        funder_year.new_funder_financial_year = funder_year.funder_financial_year
        funder_year.funder_financial_year = funder_year.original_funder_financial_year
        funder_year.save()


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0096_remove_funderyear_unique_funder_year_and_more"),
    ]

    operations = [
        migrations.RunPython(update_funder_financial_year, migrations.RunPython.noop),
    ]