# Generated by Django 5.0.6 on 2024-06-01 13:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0045_grant_beneficiary_location_ctry_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="funderyear",
            name="date_added",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
