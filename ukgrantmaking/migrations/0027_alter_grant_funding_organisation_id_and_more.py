# Generated by Django 5.0.4 on 2024-05-01 11:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ukgrantmaking", "0026_alter_currencyconverter_rate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grant",
            name="funding_organisation_id",
            field=models.CharField(
                blank=True, db_index=True, max_length=255, null=True
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="funding_organisation_name",
            field=models.CharField(
                blank=True, db_index=True, max_length=255, null=True
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="funding_organisation_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Grantmaking Organisation", "Grantmaking Organisation"),
                    ("Lottery Distributor", "Lottery Distributor"),
                    ("Central Government", "Central Government"),
                    ("Local Government", "Local Government"),
                    ("Devolved Government", "Devolved Government"),
                ],
                db_index=True,
                max_length=50,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="inclusion",
            field=models.CharField(
                choices=[
                    ("Included", "Included"),
                    ("Excluded", "Excluded"),
                    ("Unsure", "Unsure"),
                ],
                db_index=True,
                default="Unsure",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="recipient_organisation_id",
            field=models.CharField(
                blank=True, db_index=True, max_length=255, null=True
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="recipient_organisation_name",
            field=models.CharField(
                blank=True, db_index=True, max_length=255, null=True
            ),
        ),
        migrations.AlterField(
            model_name="grant",
            name="recipient_type",
            field=models.CharField(
                choices=[
                    ("Organisation", "Organisation"),
                    ("Individual", "Individual"),
                ],
                db_index=True,
                default="Organisation",
                max_length=50,
            ),
        ),
    ]
