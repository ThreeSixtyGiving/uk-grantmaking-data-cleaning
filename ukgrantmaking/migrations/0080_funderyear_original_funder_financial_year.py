# Generated by Django 5.0.6 on 2024-11-18 15:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0079_alter_funderfinancialyear_financial_year_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="funderyear",
            name="original_funder_financial_year",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="new_funder_years",
                to="ukgrantmaking.funderfinancialyear",
            ),
        ),
    ]