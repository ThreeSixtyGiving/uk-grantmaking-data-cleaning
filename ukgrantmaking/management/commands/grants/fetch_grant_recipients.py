import djclick as click
import numpy as np
import pandas as pd
from django.db import transaction
from django.db.models import Count, F, Sum
from django.db.models.functions import Coalesce

from ukgrantmaking.models import Grant, GrantRecipient, GrantRecipientYear
from ukgrantmaking.utils.text import to_titlecase


@click.command()
@click.argument("db_con", envvar="FTC_DB_URL")
def grant_recipients(db_con):
    all_recipients_query = (
        Grant.objects.exclude(recipient_organisation_id__isnull=True)
        .exclude(recipient_type=Grant.RecipientType.INDIVIDUAL)
        .exclude(recipient_organisation_name__isnull=True)
        .values(
            "recipient_organisation_name",
        )
        .order_by("-award_date")
        .annotate(
            recipient_id=Coalesce("recipient_id", "recipient_organisation_id"),
            recipient_type=Coalesce("recipient_type_manual", "recipient_type"),
            grants=Count("grant_id"),
            grant_amount=Sum("amount_awarded_GBP"),
        )
    )
    all_recipients = (
        pd.DataFrame(all_recipients_query)
        .groupby("recipient_id")
        .agg(
            {
                "recipient_organisation_name": "first",
                "recipient_type": "first",
                "grants": "sum",
                "grant_amount": "sum",
            }
        )
    )

    # create missing recipients
    existing_recipients = GrantRecipient.objects.values_list("recipient_id", flat=True)

    missing_recipients = all_recipients[~all_recipients.index.isin(existing_recipients)]

    with transaction.atomic():
        to_create = []
        with click.progressbar(
            missing_recipients.itertuples(),
            length=len(missing_recipients),
            label="Creating new recipients",
        ) as bar:
            for recipient in bar:
                to_create.append(
                    GrantRecipient(
                        recipient_id=recipient.Index,
                        type=recipient.recipient_type,
                        name_registered=recipient.recipient_organisation_name,
                    )
                )
        GrantRecipient.objects.bulk_create(to_create)

    # make sure all recipients are shown in the grants table
    Grant.objects.filter(
        recipient_id__isnull=True, recipient_organisation_id__in=existing_recipients
    ).exclude(recipient_organisation_id__isnull=True).exclude(
        recipient_organisation_name__isnull=True
    ).update(recipient_id=F("recipient_organisation_id"))

    # update existing recipients
    existing_recipient_records = all_recipients[
        all_recipients.index.isin(existing_recipients)
    ]

    with transaction.atomic():
        to_update = []
        with click.progressbar(
            existing_recipient_records.itertuples(),
            length=len(existing_recipient_records),
            label="Updating recipient records",
        ) as bar:
            for recipient in bar:
                to_update.append(
                    GrantRecipient(
                        recipient_id=recipient.Index,
                        type=recipient.recipient_type,
                        name_registered=recipient.recipient_organisation_name,
                    )
                )
        GrantRecipient.objects.bulk_update(to_create, ["type", "name_registered"])

    # get list of org IDs
    org_cache = {org.recipient_id: org for org in GrantRecipient.objects.all()}
    org_ids = tuple(org_cache.keys())

    # get updated names and date of registration from FTC
    org_records = pd.read_sql(
        """
        SELECT org_id,
            name,
            "dateRegistered",
            "dateRemoved",
            "active"
        FROM ftc_organisation
        WHERE org_id IN %(org_id)s
        """,
        params={"org_id": org_ids},
        con=db_con,
    )
    with transaction.atomic():
        with click.progressbar(
            org_records.itertuples(),
            length=len(org_records),
            label="Updating recipient data from FTC",
        ) as bar:
            for org_record in bar:
                org_cache[org_record.org_id].name_registered = to_titlecase(
                    org_record.name
                )
                org_cache[
                    org_record.org_id
                ].date_of_registration = org_record.dateRegistered
                org_cache[org_record.org_id].date_of_removal = org_record.dateRemoved
                org_cache[org_record.org_id].active = org_record.active
        GrantRecipient.objects.bulk_update(
            org_cache.values(),
            ["name_registered", "date_of_registration", "date_of_removal", "active"],
        )

    finance_records = pd.read_sql(
        """
        SELECT charity_id AS org_id,
            fyend AS financial_year_end,
            fystart AS financial_year_start,
            income,
            spending,
            employees
        FROM charity_charityfinancial
        WHERE charity_id IN %(org_id)s
        """,
        params={"org_id": org_ids},
        con=db_con,
    )
    with transaction.atomic():
        with click.progressbar(
            finance_records.replace({np.nan: None}).itertuples(),
            length=len(finance_records),
            label="Updating recipient finances from FTC",
        ) as bar:
            for financial_record in bar:
                if financial_record.org_id not in org_cache:
                    org = GrantRecipientYear.objects.get(org_id=financial_record.org_id)
                    org_cache[financial_record.org_id] = org
                else:
                    org = org_cache[financial_record.org_id]
                funder_year, created = GrantRecipientYear.objects.update_or_create(
                    recipient=org,
                    financial_year_end=financial_record.financial_year_end,
                    defaults=dict(
                        financial_year_start=financial_record.financial_year_start,
                        income_registered=financial_record.income,
                        spending_registered=financial_record.spending,
                        employees_registered=financial_record.employees,
                    ),
                )
