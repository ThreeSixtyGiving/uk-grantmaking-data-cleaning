# Generated by Django 5.0.6 on 2024-11-18 13:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0078_alter_funderyear_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="funderfinancialyear",
            name="financial_year",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="funder_financial_years",
                to="ukgrantmaking.financialyear",
            ),
        ),
        migrations.AlterField(
            model_name="funderfinancialyear",
            name="funder",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="funder_financial_years",
                to="ukgrantmaking.funder",
            ),
        ),
    ]
