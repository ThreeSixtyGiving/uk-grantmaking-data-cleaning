import logging

import djclick as click
import numpy as np
import pandas as pd
from django.db import transaction
from django.db.models import Count, F, Sum
from django.db.models.functions import Coalesce

from ukgrantmaking.models.financial_years import FinancialYear
from ukgrantmaking.models.grant import Grant, GrantRecipient, GrantRecipientYear
from ukgrantmaking.utils import do_batched_update
from ukgrantmaking.utils.text import to_titlecase

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@click.command()
@click.argument("db_con", envvar="FTC_DB_URL")
def grant_recipients(db_con):
    with transaction.atomic():
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
                recipient_type=Coalesce(
                    "recipient_type_manual", "recipient_type_registered"
                ),
                grants=Count("grant_id"),
                grant_amount=Sum("amount_awarded_GBP"),
            )
        )

        logger.info("Fetching all recipients")
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
        logger.info(f"Fetched {len(all_recipients):,.0f} recipients")

        # create missing recipients
        existing_recipients = GrantRecipient.objects.values_list(
            "recipient_id", flat=True
        )
        logger.info(f"Found {len(existing_recipients):,.0f} existing recipients")

        missing_recipients = all_recipients[
            ~all_recipients.index.isin(existing_recipients)
        ]
        logger.info(
            f"Need to create recipient records for {len(missing_recipients):,.0f} missing recipients"
        )

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
        logger.info(f"Created {len(to_create):,.0f} missing recipients")

        # make sure all recipients are shown in the grants table
        logger.info("Ensure recipients are shown in the grants table")
        Grant.objects.filter(
            recipient_id__isnull=True, recipient_organisation_id__in=existing_recipients
        ).exclude(recipient_organisation_id__isnull=True).exclude(
            recipient_organisation_name__isnull=True
        ).update(recipient_id=F("recipient_organisation_id"))

        # update existing recipients
        existing_recipient_records = all_recipients[
            all_recipients.index.isin(existing_recipients)
        ]

        logger.info("Updating existing recipients")
        with click.progressbar(
            existing_recipient_records.itertuples(),
            length=len(existing_recipient_records),
            label="Updating recipient records",
        ) as bar:

            def iterate_existing_recipient():
                for recipient in bar:
                    yield dict(
                        recipient_id=recipient.Index,
                        type=recipient.recipient_type,
                        name_registered=recipient.recipient_organisation_name,
                    )

            do_batched_update(
                GrantRecipient,
                iterate_existing_recipient(),
                unique_fields=["recipient_id"],
                update_fields=[
                    "type",
                    "name_registered",
                ],
            )
        logger.info(f"Updated {len(to_create):,.0f} existing recipients")

        # get list of org IDs
        org_ids = tuple(GrantRecipient.objects.values_list("recipient_id", flat=True))

        # get updated names and date of registration from FTC
        logger.info("Fetching recipient data from FTC")
        org_records = pd.read_sql(
            """
            WITH c AS (
                SELECT 'GB-CHC-' || registered_charity_number AS org_id,
                    array_agg(classification_description) FILTER (WHERE classification_type = 'How') AS how,
                    array_agg(classification_description) FILTER (WHERE classification_type = 'What') AS what,
                    array_agg(classification_description) FILTER (WHERE classification_type = 'Who') AS who 
                FROM charity_ccewcharityclassification 
                WHERE linked_charity_number = 0
                GROUP BY 1
            ),
            l AS (
                 SELECT org_id,
                    array_agg(DISTINCT l.geo_laua) FILTER (WHERE "locationType" = 'HQ' AND l.geo_laua IS NOT NULL) AS la_hq,
                    json_object_agg(DISTINCT l.geo_laua, la."name") FILTER (WHERE "locationType" = 'HQ' AND l.geo_laua IS NOT NULL) AS la_hq_name,
                    array_agg(DISTINCT l.geo_laua) FILTER (WHERE "locationType" = 'AOO' AND l.geo_laua IS NOT NULL) AS la_aoo,
                    json_object_agg(DISTINCT l.geo_laua, la."name") FILTER (WHERE "locationType" = 'AOO' AND l.geo_laua IS NOT NULL) AS la_aoo_name,
                    array_agg(DISTINCT l.geo_rgn) FILTER (WHERE "locationType" = 'HQ' AND l.geo_rgn IS NOT NULL) AS rgn_hq,
                    json_object_agg(DISTINCT l.geo_rgn, rgn."name") FILTER (WHERE "locationType" = 'HQ' AND l.geo_rgn IS NOT NULL) AS rgn_hq_name,
                    array_agg(DISTINCT l.geo_rgn) FILTER (WHERE "locationType" = 'AOO' AND l.geo_rgn IS NOT NULL) AS rgn_aoo,
                    json_object_agg(DISTINCT l.geo_rgn, rgn."name") FILTER (WHERE "locationType" = 'AOO' AND l.geo_rgn IS NOT NULL) AS rgn_aoo_name,
                    array_agg(DISTINCT l.geo_ctry) FILTER (WHERE "locationType" = 'HQ' AND l.geo_ctry IS NOT NULL) AS ctry_hq,
                    json_object_agg(DISTINCT l.geo_ctry, ctry."name") FILTER (WHERE "locationType" = 'HQ' AND l.geo_ctry IS NOT NULL) AS ctry_hq_name,
                    array_agg(DISTINCT l.geo_ctry) FILTER (WHERE "locationType" = 'AOO' AND l.geo_ctry IS NOT NULL) AS ctry_aoo,
                    json_object_agg(DISTINCT l.geo_ctry, ctry."name") FILTER (WHERE "locationType" = 'AOO' AND l.geo_ctry IS NOT NULL) AS ctry_aoo_name,
                    array_agg(DISTINCT l.geo_iso) FILTER (WHERE "locationType" = 'AOO' AND l.geo_iso IS NOT NULL AND l.geo_iso != 'GB') AS overseas_aoo,
                    json_object_agg(DISTINCT l.geo_iso, iso."name") FILTER (WHERE "locationType" = 'AOO' AND l.geo_iso IS NOT NULL AND l.geo_iso != 'GB') AS overseas_aoo_name,
                    SUM(CASE WHEN l.geo_rgn = 'E12000007' AND "locationType" = 'HQ' THEN 1 ELSE 0 END) > 0 AS london_hq,
                    SUM(CASE WHEN l.geo_rgn = 'E12000007' AND "locationType" = 'AOO' THEN 1 ELSE 0 END) > 0 AS london_aoo
                FROM ftc_organisationlocation l
                    LEFT OUTER JOIN geo_geolookup rgn
                        ON l.geo_rgn = rgn."geoCode"
                    LEFT OUTER JOIN geo_geolookup ctry
                        ON l.geo_ctry = ctry."geoCode"
                    LEFT OUTER JOIN geo_geolookup la
                        ON l.geo_laua = la."geoCode"
                    LEFT OUTER JOIN geo_geolookup iso
                        ON l.geo_iso = iso."geoCode"
                GROUP BY 1
            ),
            s AS (
                SELECT c.org_id,
                    ve.title AS scale
                FROM ftc_vocabulary v
                    INNER JOIN ftc_vocabularyentries ve
                        ON v.id = ve.vocabulary_id 
                    INNER JOIN ftc_organisationclassification c
                        ON ve.id = c.vocabulary_id 
                WHERE v.slug = 'scale'
            )
            SELECT o.org_id,
                name,
                "dateRegistered",
                "dateRemoved",
                "active",
                c.how,
                c.what,
                c.who,
                o."postalCode" AS postcode,
                la_hq[1] as la_hq,
                la_hq_name->>la_hq[1] as la_hq_name,
                la_aoo,
                la_aoo_name,
                rgn_hq[1] as rgn_hq,
                rgn_hq_name->>rgn_hq[1] as rgn_hq_name,
                rgn_aoo,
                rgn_aoo_name,
                ctry_hq[1] as ctry_hq,
                ctry_hq_name->>ctry_hq[1] as ctry_hq_name,
                ctry_aoo,
                ctry_aoo_name,
                overseas_aoo,
                overseas_aoo_name,
                london_hq,
                london_aoo,
                s.scale as scale_registered
            FROM ftc_organisation o
                LEFT OUTER JOIN c
                    ON o.org_id = c.org_id
                LEFT OUTER JOIN l
                    ON o.org_id = l.org_id
                LEFT OUTER JOIN s
                    ON o.org_id = s.org_id
            WHERE o.org_id IN %(org_id)s
            """,
            params={"org_id": org_ids},
            con=db_con,
        )
        logger.info(f"Fetched {len(org_records):,.0f} recipient records from FTC")

        logger.info("Updating records with data from FTC")
        with click.progressbar(
            org_records.itertuples(),
            length=len(org_records),
            label="Updating recipient data from FTC",
        ) as bar:

            def iterate_recipient():
                for org_record in bar:
                    yield dict(
                        recipient_id=org_record.org_id,
                        name_registered=to_titlecase(org_record.name),
                        date_of_registration=org_record.dateRegistered,
                        date_of_removal=org_record.dateRemoved,
                        active=org_record.active,
                        postcode=org_record.postcode,
                        how=org_record.how,
                        what=org_record.what,
                        who=org_record.who,
                        la_hq=org_record.la_hq,
                        la_hq_name=org_record.la_hq_name,
                        la_aoo=org_record.la_aoo,
                        la_aoo_name=org_record.la_aoo_name,
                        rgn_hq=org_record.rgn_hq,
                        rgn_hq_name=org_record.rgn_hq_name,
                        rgn_aoo=org_record.rgn_aoo,
                        rgn_aoo_name=org_record.rgn_aoo_name,
                        ctry_hq=org_record.ctry_hq,
                        ctry_hq_name=org_record.ctry_hq_name,
                        ctry_aoo=org_record.ctry_aoo,
                        ctry_aoo_name=org_record.ctry_aoo_name,
                        overseas_aoo=org_record.overseas_aoo,
                        overseas_aoo_name=org_record.overseas_aoo_name,
                        london_hq=org_record.london_hq,
                        london_aoo=org_record.london_aoo,
                        scale_registered=org_record.scale_registered,
                    )

            do_batched_update(
                GrantRecipient,
                iterate_recipient(),
                unique_fields=["recipient_id"],
                update_fields=[
                    "name_registered",
                    "date_of_registration",
                    "date_of_removal",
                    "active",
                    "postcode",
                    "how",
                    "what",
                    "who",
                    "la_hq",
                    "la_hq_name",
                    "la_aoo",
                    "la_aoo_name",
                    "rgn_hq",
                    "rgn_hq_name",
                    "rgn_aoo",
                    "rgn_aoo_name",
                    "ctry_hq",
                    "ctry_hq_name",
                    "ctry_aoo",
                    "ctry_aoo_name",
                    "overseas_aoo",
                    "overseas_aoo_name",
                    "london_hq",
                    "london_aoo",
                    "scale_registered",
                ],
            )
        logger.info(f"Updated {len(org_records):,.0f} records with data from FTC")

        logger.info("Fetching financial records from FTC")
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
        logger.info(f"Fetched {len(finance_records):,.0f} financial records from FTC")

        # Add in financial year
        # get all financial years
        for financial_year in FinancialYear.objects.all():
            finance_records.loc[
                (
                    finance_records["financial_year_end"]
                    >= financial_year.funders_start_date
                )
                & (
                    finance_records["financial_year_end"]
                    <= financial_year.funders_end_date
                ),
                "financial_year",
            ] = financial_year.fy

        logger.info("Updating financial records with data from FTC")
        with click.progressbar(
            finance_records.replace({np.nan: None}).itertuples(),
            length=len(finance_records),
            label="Updating recipient finances from FTC",
        ) as bar:

            def iterate_grant_recipient_year():
                for financial_record in bar:
                    yield dict(
                        recipient_id=financial_record.org_id,
                        financial_year_end=financial_record.financial_year_end,
                        financial_year_start=financial_record.financial_year_start,
                        income_registered=financial_record.income,
                        spending_registered=financial_record.spending,
                        employees_registered=financial_record.employees,
                        financial_year_id=financial_record.financial_year,
                    )

            do_batched_update(
                GrantRecipientYear,
                iterate_grant_recipient_year(),
                unique_fields=[
                    "recipient_id",
                    "financial_year_end",
                ],
                update_fields=[
                    "financial_year_start",
                    "income_registered",
                    "spending_registered",
                    "employees_registered",
                    "financial_year_id",
                ],
            )
        logger.info(
            f"Updated {len(finance_records):,.0f} financial records with data from FTC"
        )
