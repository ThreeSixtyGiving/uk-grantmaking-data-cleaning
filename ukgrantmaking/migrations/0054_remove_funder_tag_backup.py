# Generated by Django 5.0.6 on 2024-11-12 12:19

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0053_auto_20241112_1215"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="funder",
            name="tag_backup",
        ),
    ]
