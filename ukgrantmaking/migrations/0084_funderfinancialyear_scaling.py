# Generated by Django 5.0.6 on 2024-11-19 09:24

import django.db.models.functions.comparison
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0083_alter_funderyear_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="funderfinancialyear",
            name="scaling",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    models.F("spending_grant_making"),
                    models.F("spending_charitable"),
                    models.F("spending"),
                    0,
                ),
                output_field=models.BigIntegerField(),
            ),
        ),
    ]