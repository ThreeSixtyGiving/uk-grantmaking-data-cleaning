# Generated by Django 5.0.4 on 2024-04-19 08:36

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0005_alter_funder_included_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="funderyear",
            options={"ordering": ["-financial_year_end"]},
        ),
        migrations.AlterUniqueTogether(
            name="funderyear",
            unique_together={("funder", "financial_year_end")},
        ),
    ]
