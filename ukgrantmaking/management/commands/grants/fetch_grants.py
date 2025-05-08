import logging
from collections import defaultdict

import djclick as click
import numpy as np
import pandas as pd
from django.db import transaction
from django.db.models import Q

from ukgrantmaking.models.financial_years import FinancialYear
from ukgrantmaking.models.grant import CurrencyConverter, Grant
from ukgrantmaking.utils import do_batched_update

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@click.command()
@click.argument("db_con", envvar="TSG_DATASTORE_URL")
def grants(db_con):
    current_fy = FinancialYear.objects.current()
    datastore_query = """
        WITH g AS materialized (SELECT * FROM view_latest_grant),
        location_source AS (
            SELECT g.grant_id,
                jsonb_array_elements(g.additional_data->'locationLookup') AS location
            FROM g
        ),
        location AS (
            SELECT grant_id,
                array_agg(DISTINCT "location"->>'rgncd') FILTER (WHERE "location"->>'source' like 'recipient%%' AND "location"->>'rgncd' IS NOT NULL) AS recipient_location_rgn,
                array_agg(DISTINCT "location"->>'ctrycd') FILTER (WHERE "location"->>'source' like 'recipient%%' AND "location"->>'ctrycd' IS NOT NULL) AS recipient_location_ctry,
                array_agg(DISTINCT "location"->>'rgncd') FILTER (WHERE "location"->>'source' like 'beneficiary%%' AND "location"->>'rgncd' IS NOT NULL) AS beneficiary_location_rgn,
                array_agg(DISTINCT "location"->>'ctrycd') FILTER (WHERE "location"->>'source' like 'beneficiary%%' AND "location"->>'ctrycd' IS NOT NULL) AS beneficiary_location_ctry
            FROM location_source
            GROUP BY grant_id
        ),
        a AS (
            SELECT g.data->>'id' AS "grant_id",
                g.data->>'title' AS "title",
                g.data->>'description' AS "description",
                g.data->>'currency' AS "currency",
                g.data->>'amountAwarded' AS "amount_awarded",
                to_date(
                    CASE WHEN g.source_data->>'identifier' = 'a00P400000RKHBiIAP' THEN '2023-04-01'
                    ELSE g.data->>'awardDate' END,
                    'YYYY-MM-DD'
                ) AS "award_date",
                g.data->'plannedDates'->0->>'duration' AS "planned_dates_duration",
                to_date(g.data->'plannedDates'->0->>'startDate', 'YYYY-MM-DD') AS "planned_dates_startDate",
                to_date(g.data->'plannedDates'->0->>'endDate', 'YYYY-MM-DD') AS "planned_dates_endDate",
                g.data->'recipientOrganization'->0->>'id' AS "recipient_organization_id",
                g.data->'recipientOrganization'->0->>'name' AS "recipient_organization_name",
                g.data->'recipientIndividual'->>'id' AS "recipient_individual_id",
                g.data->'recipientIndividual'->>'name' AS "recipient_individual_name",
                g.data->'toIndividualsDetails'->>'primaryGrantReason' AS "recipient_individual_primary_grant_reason",
                g.data->'toIndividualsDetails'->>'secondaryGrantReason' AS "recipient_individual_secondary_grant_reason",
                g.data->'toIndividualsDetails'->>'grantPurpose' AS "recipient_individual_grant_purpose",
                CASE WHEN g.data->>'recipientOrganization' IS NOT NULL THEN 'Organisation' ELSE 'Individual' END AS "recipient_type",
                g.data->'fundingOrganization'->0->>'id' AS "funding_organization_id",
                g.data->'fundingOrganization'->0->>'name' AS "funding_organization_name",
                g.additional_data->>'TSGFundingOrgType' AS "funding_organization_type",
                COALESCE(
                    g.data->'Managed by'->>'Organisation Name',
                    g.data->'fundingOrganization'->0->>'department'
                ) AS "funding_organization_department",
                g.data->>'regrantType' AS "regrant_type",
                g.data->>'locationScope' AS "location_scope",
                g.data->'grantProgramme'->0->>'title' AS "grant_programme_title",
                g.source_data->'publisher'->>'prefix' AS "publisher_prefix",
                g.source_data->'publisher'->>'name' AS "publisher_name",
                g.source_data->>'license' AS "license",
                recipient_location_rgn[1] AS "recipient_location_rgn",
                recipient_location_ctry[1] AS "recipient_location_ctry",
                beneficiary_location_rgn[1] AS "beneficiary_location_rgn",
                beneficiary_location_ctry[1] AS "beneficiary_location_ctry"
            FROM g
                LEFT OUTER JOIN location
                    ON g.grant_id = location.grant_id
        )
        SELECT * FROM a
        WHERE a.award_date >= %(start_date)s
            AND a.award_date <= %(end_date)s
    """

    # get updated names and date of registration from FTC
    logger.info("Fetching grants from datastore")
    df = pd.read_sql(
        datastore_query,
        params={
            "start_date": current_fy.grants_start_date,
            "end_date": current_fy.grants_end_date,
        },
        con=db_con,
        index_col="grant_id",
    )
    logger.info(f"Found {len(df):,.0f} grants")

    # To clean the data we need to make sure that the values are in the right format.

    # Next, the `planned_dates_duration` should also be a number. We use
    # float instead of integer because it allows for null values.
    df["planned_dates_duration"] = df["planned_dates_duration"].astype(float)

    # We can also use the `planned_dates_startDate` and `planned_dates_endDate`
    # fields to fill in any gaps. We need to convert them to dates and
    # then find the gap between them.

    # calculate duration as python timedelta
    duration = pd.to_datetime(df["planned_dates_endDate"], utc=True) - pd.to_datetime(
        df["planned_dates_startDate"], utc=True
    )
    # convert into months
    duration = duration.divide(np.timedelta64(30, "D"))
    # use ceiling to get the whole number of months
    duration = np.abs(np.ceil(duration))

    df["planned_dates_duration"] = df["planned_dates_duration"].fillna(duration)

    # add National Lottery data
    nl_api_vars = {
        "page": 1,
        "limit": 10,
        "ordering": "-award_date",
        "good_cause_area": "",
        "funding_org": "",
        "region": "",
        "local_authority": "",
        "uk_constituency": "",
        "ward": "",
        "recipient_org": "",
        "award_date_after": current_fy.grants_start_date,
        "award_date_before": current_fy.grants_end_date,
        "amount_awarded_min": "",
        "amount_awarded_max": "",
        "search": "",
    }
    nl_api_url = (
        "https://nationallottery.dcms.gov.uk/api/v1/grants/csv-export/?"
        + "&".join([f"{k}={v}" for k, v in nl_api_vars.items()])
    )
    logger.info("Fetching grants from National Lottery")
    nl = pd.read_csv(nl_api_url, parse_dates=["Award Date"])
    logger.info(f"Found {len(nl):,.0f} National Lottery grants")

    nl_column_rename = {
        "Identifier": "grant_id",
        "Title": "title",
        "Description": "description",
        "Currency": "currency",
        "Amount Awarded": "amount_awarded",
        "Award Date": "award_date",
        "Recipient Org:Identifier": "recipient_organization_id",
        "Recipient Org:Name": "recipient_organization_name",
        # 'Recipient Org:Ward': "",
        # 'Recipient Org:UK Constituency': "",
        # 'Recipient Org:Local Authority': "",
        # 'Recipient Org:Region': "",
        "Funding Org:Identifier": "funding_organization_id",
        "Funding Org:Name": "funding_organization_name",
        # 'Good Cause Area': "",
        # 'Last Modified': "",
    }
    nl = (
        nl.rename(columns=nl_column_rename)[nl_column_rename.values()]
        .assign(
            recipient_type="Organisation",
            funding_oganization_type="National Lottery Distributor",
            publisher_prefix="dcms-nationallottery",
            publisher_name="The National Lottery",
            license="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        )
        .set_index("grant_id")
    )
    nl.loc[
        (
            nl["recipient_organization_name"]
            .str.strip()
            .isin(["Grant to Individual", "Grant Awarded to Individual"])
        )
        | nl["description"].isin(["Athlete Performance Award"]),
        "recipient_type",
    ] = "Individual"

    # We want to exclude any grants from the National Lottery dataset that are
    # present in the main Dataframe, so we can merge them without duplicating grants.

    # Setup the exclusion variable with False as the default value.
    nl.loc[:, "exclude"] = False

    # Next, look for any rows where the grant ID is the same.

    # National Lottery Community Fund grants have a slightly different format, but the same ID.
    index_match = pd.Index(
        [x.replace("DCMS-tnlcomfund-", "360G-tnlcomfund-") for x in nl.index]
    )

    # set any grants where the index match is the same to exclude
    nl.loc[index_match.isin(df.index), "exclude"] = True

    # Next merge the two datasets together based on `amount_awarded`, `award_date`,
    # `recipient_organization_name` and `funding_organization_id`.

    # Any grants where these fields match are marked as excluded.
    match_fields = [
        "title",
        "amount_awarded",
        "award_date",
        "recipient_organization_name",
        "funding_organization_id",
    ]
    merged = (
        nl.assign(
            amount_awarded=nl.amount_awarded.astype(float),
            award_date=pd.to_datetime(nl.award_date, utc=True, format="ISO8601"),
            grant_id=nl.index,
            title=nl.title.str.strip().str.lower(),
            recipient_organization_name=nl.recipient_organization_name.str.strip().str.lower(),
        )
        .merge(
            df.assign(
                amount_awarded=df.amount_awarded.astype(float),
                award_date=pd.to_datetime(df.award_date, utc=True, format="ISO8601"),
                grant_id=df.index,
                title=df.title.str.strip().str.lower(),
                recipient_organization_name=df.recipient_organization_name.str.strip().str.lower(),
            ),
            how="left",
            left_on=match_fields,
            right_on=match_fields,
            suffixes=("_nl", "_df"),
        )
        .query("grant_id_df.notnull() & grant_id_nl.notnull()")
        .drop_duplicates()
    )

    # set any grants which appear in both datasets to exclude
    nl.loc[nl.index.isin(merged["grant_id_nl"]), "exclude"] = True

    logger.info(
        f"Excluding {len(nl[nl['exclude']]):,.0f} grants from National Lottery dataset"
    )

    # Merge the National Lottery dataset into the main dataset.
    df = pd.concat(
        [
            df,
            nl[~nl["exclude"]].drop(columns=["exclude"]),
        ]
    )

    # drop any duplicate by grant_id (the index)
    # @TODO: could redo the grant_id so that it's a unique identifier
    duplicated = df[df.index.duplicated(keep=False)]
    logger.info(f"Dropping {len(duplicated):,.0f} duplicate grants based on grant_id")
    for funder_id, funder_name, count in (
        duplicated.groupby(["funding_organization_id", "funding_organization_name"])
        .size()
        .reset_index()
        .values
    ):
        logger.info(f"   {funder_id}: {funder_name}: {count:,.0f} duplicates")
    df = df[~df.index.duplicated(keep="first")]

    # Start with the `amount_awarded` column, which should be an integer.
    df["amount_awarded"] = df["amount_awarded"].astype(float)

    # Make sure award date is a date
    for field in ["award_date", "planned_dates_startDate", "planned_dates_endDate"]:
        df[field] = pd.to_datetime(df[field], utc=True, format="ISO8601").dt.date

    # set amount awarded GBP to same as amount awarded where currency is GBP
    df.loc[df["currency"] == "GBP", "amount_awarded_gbp"] = df.loc[
        df["currency"] == "GBP", "amount_awarded"
    ]

    # Add in financial year
    # get all financial years
    for financial_year in FinancialYear.objects.all():
        df.loc[
            (df["award_date"] >= financial_year.grants_start_date)
            & (df["award_date"] <= financial_year.grants_end_date),
            "financial_year",
        ] = financial_year.fy

    with transaction.atomic():
        logger.info("Saving currencies to database")
        currency_result = defaultdict(int)
        for currency, awarddate in (
            df[~df["currency"].eq("GBP")]
            .groupby(["currency", "award_date"])
            .size()
            .index
        ):
            _, created = CurrencyConverter.objects.get_or_create(
                currency=currency,
                date=awarddate,
                defaults={"rate": 1},
            )
            if created:
                currency_result["CurrencyConverter created"] += 1
            else:
                currency_result["CurrencyConverter found"] += 1
        for key, value in currency_result.items():
            logger.info(f"{key}: {value:,.0f}")

        logger.info(f"Saving {len(df):,.0f} grants to database")
        with click.progressbar(
            df.replace({np.nan: None}).itertuples(),
            length=len(df),
            label="Saving Grant records",
        ) as bar:

            def iterate_grants():
                for grant in bar:
                    yield dict(
                        grant_id=grant.Index,
                        title=grant.title,
                        description=grant.description,
                        currency=grant.currency,
                        amount_awarded=grant.amount_awarded,
                        amount_awarded_GBP=grant.amount_awarded_gbp,
                        award_date=grant.award_date,
                        planned_dates_duration=grant.planned_dates_duration,
                        planned_dates_startDate=(
                            None
                            if pd.isnull(grant.planned_dates_startDate)
                            else grant.planned_dates_startDate
                        ),
                        planned_dates_endDate=(
                            None
                            if pd.isnull(grant.planned_dates_endDate)
                            else grant.planned_dates_endDate
                        ),
                        recipient_organisation_id=grant.recipient_organization_id,
                        recipient_organisation_name=grant.recipient_organization_name,
                        recipient_individual_id=grant.recipient_individual_id,
                        recipient_individual_name=grant.recipient_individual_name,
                        recipient_individual_primary_grant_reason=grant.recipient_individual_primary_grant_reason,
                        recipient_individual_secondary_grant_reason=grant.recipient_individual_secondary_grant_reason,
                        recipient_individual_grant_purpose=grant.recipient_individual_grant_purpose,
                        recipient_type_registered=grant.recipient_type,
                        funding_organisation_id=grant.funding_organization_id,
                        funding_organisation_name=grant.funding_organization_name,
                        funding_organisation_department=grant.funding_organization_department,
                        funding_organisation_type=grant.funding_organization_type,
                        regrant_type_registered=grant.regrant_type,
                        location_scope=grant.location_scope,
                        grant_programme_title=grant.grant_programme_title,
                        publisher_prefix=grant.publisher_prefix,
                        publisher_name=grant.publisher_name,
                        license=grant.license,
                        financial_year_id=grant.financial_year,
                    )

            do_batched_update(
                Grant,
                iterate_grants(),
                unique_fields=[
                    "grant_id",
                ],
                update_fields=[
                    "title",
                    "description",
                    "currency",
                    "amount_awarded",
                    "amount_awarded_GBP",
                    "award_date",
                    "planned_dates_duration",
                    "planned_dates_startDate",
                    "planned_dates_endDate",
                    "recipient_organisation_id",
                    "recipient_organisation_name",
                    "recipient_individual_id",
                    "recipient_individual_name",
                    "recipient_individual_primary_grant_reason",
                    "recipient_individual_secondary_grant_reason",
                    "recipient_individual_grant_purpose",
                    "recipient_type_registered",
                    "funding_organisation_id",
                    "funding_organisation_name",
                    "funding_organisation_department",
                    "funding_organisation_type",
                    "regrant_type_registered",
                    "location_scope",
                    "grant_programme_title",
                    "publisher_prefix",
                    "publisher_name",
                    "license",
                    "financial_year_id",
                ],
            )
        logger.info(f"Saved {len(df):,.0f} grants to database")

        # update grant inclusions
        logger.info("Updating grant inclusions")
        logger.info(
            "All grants not in central or devolved government are included by default"
        )
        updated = (
            Grant.objects.filter(
                inclusion=Grant.InclusionStatus.UNSURE,
            )
            .exclude(
                funding_organisation_type__in=[
                    Grant.FunderType.CENTRAL_GOVERNMENT,
                    Grant.FunderType.LOCAL_GOVERNMENT,
                    Grant.FunderType.DEVOLVED_GOVERNMENT,
                ]
            )
            .update(inclusion=Grant.InclusionStatus.INCLUDED)
        )
        logger.info(f"{updated:,.0f} grants updated to included")

        logger.info(
            "All grants with a recipient organisation ID starting with GB-CHC-, GB-SC- or GB-NIC- are included by default"
        )
        updated = (
            Grant.objects.filter(
                inclusion=Grant.InclusionStatus.UNSURE,
            )
            .filter(
                Q(recipient_organisation_id__startswith="GB-CHC-")
                | Q(recipient_organisation_id__startswith="GB-SC-")
                | Q(recipient_organisation_id__startswith="GB-NIC-")
            )
            .update(inclusion=Grant.InclusionStatus.INCLUDED)
        )
        logger.info(f"{updated:,.0f} grants updated to included")
