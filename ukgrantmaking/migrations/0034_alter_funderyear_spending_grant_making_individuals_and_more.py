# Generated by Django 5.0.4 on 2024-05-02 10:18

import django.db.models.functions.comparison
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "ukgrantmaking",
            "0033_funderyear_spending_grant_making_individuals_360giving_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="funderyear",
            name="spending_grant_making",
            field=models.GeneratedField(
                expression=models.Case(
                    models.When(
                        django.db.models.lookups.IsNull(
                            models.F("spending_grant_making_individuals"), False
                        )
                        | django.db.models.lookups.IsNull(
                            models.F("spending_grant_making_institutions"), False
                        ),
                        then=(
                            django.db.models.functions.comparison.Coalesce(
                                models.F("spending_grant_making_individuals"), 0
                            )
                            + django.db.models.functions.comparison.Coalesce(
                                models.F("spending_grant_making_institutions"), 0
                            )
                        ),
                    )
                ),
                output_field=models.BigIntegerField(),
                db_persist=True,
            ),
        ),
        migrations.RemoveField(
            model_name="funderyear",
            name="spending_grant_making_individuals",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    "spending_grant_making_individuals_manual",
                    "spending_grant_making_individuals_360Giving",
                    "spending_grant_making_individuals_registered",
                ),
                output_field=models.BigIntegerField(),
            ),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="spending_grant_making_individuals",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    "spending_grant_making_individuals_manual",
                    "spending_grant_making_individuals_registered",
                    "spending_grant_making_individuals_360Giving",
                ),
                output_field=models.BigIntegerField(),
            ),
        ),
        migrations.RemoveField(
            model_name="funderyear",
            name="spending_grant_making_institutions",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    "spending_grant_making_institutions_manual",
                    "spending_grant_making_institutions_360Giving",
                    "spending_grant_making_institutions_registered",
                ),
                output_field=models.BigIntegerField(),
            ),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="spending_grant_making_institutions",
            field=models.GeneratedField(
                db_persist=True,
                expression=django.db.models.functions.comparison.Coalesce(
                    "spending_grant_making_institutions_manual",
                    "spending_grant_making_institutions_registered",
                    "spending_grant_making_institutions_360Giving",
                ),
                output_field=models.BigIntegerField(),
            ),
        ),
        migrations.AddField(
            model_name="funderyear",
            name="spending_grant_making",
            field=models.GeneratedField(
                expression=models.Case(
                    models.When(
                        django.db.models.lookups.IsNull(
                            models.F("spending_grant_making_individuals"), False
                        )
                        | django.db.models.lookups.IsNull(
                            models.F("spending_grant_making_institutions"), False
                        ),
                        then=(
                            django.db.models.functions.comparison.Coalesce(
                                models.F("spending_grant_making_individuals"), 0
                            )
                            + django.db.models.functions.comparison.Coalesce(
                                models.F("spending_grant_making_institutions"), 0
                            )
                        ),
                    )
                ),
                output_field=models.BigIntegerField(),
                db_persist=True,
            ),
        ),
    ]