# Generated by Django 5.0.4 on 2024-05-01 10:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0025_currencyconverter_grant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="currencyconverter",
            name="rate",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=16, null=True
            ),
        ),
    ]
