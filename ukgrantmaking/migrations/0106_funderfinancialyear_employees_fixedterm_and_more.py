# Generated by Django 5.0.6 on 2025-01-22 11:04

import django.db.models.functions.comparison
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0105_alter_cleaningstatus_sort_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="funderfinancialyear",
            name="employees_fixedterm",
            field=models.BigIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="funderfinancialyear",
            name="employees_permanent",
            field=models.BigIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="funderfinancialyear",
            name="employees_selfemployed",
            field=models.BigIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_fixedterm_manual",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_fixedterm_registered",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_permanent_manual",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_permanent_registered",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_selfemployed_manual",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_selfemployed_registered",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_fixedterm",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    "employees_fixedterm_manual", "employees_fixedterm_registered"
                ),
                output_field=models.BigIntegerField(),
            ),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_permanent",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    "employees_permanent_manual", "employees_permanent_registered"
                ),
                output_field=models.BigIntegerField(),
            ),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="employees_selfemployed",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    "employees_selfemployed_manual", "employees_selfemployed_registered"
                ),
                output_field=models.BigIntegerField(),
            ),
        ),
    ]
