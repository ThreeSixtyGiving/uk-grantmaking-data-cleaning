# Generated by Django 5.0.6 on 2024-11-15 07:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0068_grant_recipient_type_registered_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grant",
            name="title",
            field=models.TextField(),
        ),
    ]
