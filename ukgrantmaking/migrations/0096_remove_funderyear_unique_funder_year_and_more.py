# Generated by Django 5.0.6 on 2024-12-16 19:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0095_alter_funderyear_unique_together_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="funderyear",
            name="unique_funder_year",
        ),
        migrations.AddField(
            model_name="funderyear",
            name="new_funder_financial_year",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="original_funder_years",
                to="ukgrantmaking.funderfinancialyear",
            ),
        ),
    ]