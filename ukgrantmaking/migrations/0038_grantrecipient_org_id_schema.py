# Generated by Django 5.0.6 on 2024-05-15 15:28

import django.db.models.expressions
import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "ukgrantmaking",
            "0037_rename_date_registered_grantrecipient_date_of_registration_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="grantrecipient",
            name="org_id_schema",
            field=models.GeneratedField(
                db_persist=True,
                expression=models.Case(
                    models.When(
                        models.Q(("recipient_id__startswith", "UKG-")),
                        then=models.Value("UKG"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "360G-")),
                        then=models.Value("UKG"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-CHC-")),
                        then=models.Value("GB-CHC"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-COH-")),
                        then=models.Value("GB-COH"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-SC-")),
                        then=models.Value("GB-SC"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-NIC-")),
                        then=models.Value("GB-NIC"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-LAE-")),
                        then=models.Value("GB-LAE"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-GOR-")),
                        then=models.Value("GB-GOR"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-SHPE-")),
                        then=models.Value("GB-SHPE"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-NHS-")),
                        then=models.Value("GB-NHS"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-LAS-")),
                        then=models.Value("GB-LAS"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-PLA-")),
                        then=models.Value("GB-PLA"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "GB-LANI-")),
                        then=models.Value("GB-LANI"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "US-EIN-")),
                        then=models.Value("US-EIN"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "XI-ROR-")),
                        then=models.Value("XI-ROR"),
                    ),
                    models.When(
                        models.Q(("recipient_id__startswith", "XI-PB-")),
                        then=models.Value("XI-PB"),
                    ),
                    default=django.db.models.functions.text.Left(
                        models.F("recipient_id"),
                        django.db.models.expressions.CombinedExpression(
                            django.db.models.functions.text.StrIndex(
                                models.F("recipient_id"), models.Value("-")
                            ),
                            "-",
                            models.Value(1),
                        ),
                    ),
                ),
                output_field=models.CharField(max_length=255),
            ),
        ),
    ]
