# Generated by Django 5.0.4 on 2024-04-18 23:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0003_alter_funder_segment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="funder",
            name="charity_number",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
