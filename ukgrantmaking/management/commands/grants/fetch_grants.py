from collections import defaultdict

import djclick as click
import numpy as np
import pandas as pd
from django.db import transaction

from ukgrantmaking.models import CurrencyConverter, Grant


@click.command()
@click.argument("db_con", envvar="TSG_DATASTORE_URL")
@click.option("--start-date", default="2022-04-01")
@click.option("--end-date", default="2023-03-31")
def grants(db_con, start_date, end_date):
    datastore_query = """
        with g as materialized (select * from view_latest_grant)
        select g.data->>'id' as "grant_id",
            g.data->>'title' as "title",
            g.data->>'description' as "description",
            g.data->>'currency' as "currency",
            g.data->>'amountAwarded' as "amount_awarded",
            g.data->>'awardDate' as "award_date",
            g.data->'plannedDates'->0->>'duration' as "planned_dates_duration",
            g.data->'plannedDates'->0->>'startDate' as "planned_dates_startDate",
            g.data->'plannedDates'->0->>'endDate' as "planned_dates_endDate",
            g.data->'recipientOrganization'->0->>'id' as "recipient_organization_id",
            g.data->'recipientOrganization'->0->>'name' as "recipient_organization_name",
            g.data->'recipientIndividual'->>'id' as "recipient_individual_id",
            g.data->'recipientIndividual'->>'name' as "recipient_individual_name",
            g.data->'toIndividualsDetails'->>'primaryGrantReason' as "recipient_individual_primary_grant_reason",
            g.data->'toIndividualsDetails'->>'secondaryGrantReason' as "recipient_individual_secondary_grant_reason",
            g.data->'toIndividualsDetails'->>'grantPurpose' as "recipient_individual_grant_purpose",
            case when g.data->>'recipientOrganization' is not null then 'Organisation' else 'Individual' end as "recipient_type",
            g.data->'fundingOrganization'->0->>'id' as "funding_organization_id",
            g.data->'fundingOrganization'->0->>'name' as "funding_organization_name",
            g.additional_data->>'TSGFundingOrgType' as "funding_organization_type",
            g.data->>'regrantType' as "regrant_type",
            g.data->>'locationScope' as "location_scope",
            g.data->'grantProgramme'->0->>'title' as "grant_programme_title",
            g.source_data->'publisher'->>'prefix' as "publisher_prefix",
            g.source_data->'publisher'->>'name' as "publisher_name",
            g.source_data->>'license' as "license"
        from g
        where to_date(g.data->>'awardDate', 'YYYY-MM-DD') >= %(start_date)s
        and to_date(g.data->>'awardDate', 'YYYY-MM-DD') <= %(end_date)s
    """

    # get updated names and date of registration from FTC
    click.secho("Fetching grants from datastore", fg="green")
    df = pd.read_sql(
        datastore_query,
        params={"start_date": start_date, "end_date": end_date},
        con=db_con,
        index_col="grant_id",
    )
    click.secho("Found {} grants".format(len(df)), fg="green")

    # To clean the data we need to make sure that the values are in the right format.

    # Next, the `planned_dates_duration` should also be a number. We use
    # float instead of integer because it allows for null values.
    df["planned_dates_duration"] = df["planned_dates_duration"].astype(float)

    # We can also use the `planned_dates_startDate` and `planned_dates_endDate`
    # fields to fill in any gaps. We need to convert them to dates and
    # then find the gap between them.

    # The `planned_dates_endDate` has some invalid date values, which we'll
    # replace before turning them into dates.
    enddate = (
        df["planned_dates_endDate"]
        .str[0:10]
        .replace(
            {
                "2022-02-30": "2022-02-28",
            }
        )
    )
    # calculate duration as python timedelta
    duration = pd.to_datetime(enddate, utc=True) - pd.to_datetime(
        df["planned_dates_startDate"].str[0:10], utc=True
    )
    # convert into months
    duration = duration.divide(np.timedelta64(30, "D"))
    # use ceiling to get the whole number of months
    duration = np.ceil(duration)

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
        "award_date_after": start_date,
        "award_date_before": end_date,
        "amount_awarded_min": "",
        "amount_awarded_max": "",
        "search": "",
    }
    nl_api_url = (
        "https://nationallottery.dcms.gov.uk/api/v1/grants/csv-export/?"
        + "&".join([f"{k}={v}" for k, v in nl_api_vars.items()])
    )
    click.secho("Fetching grants from National Lottery", fg="green")
    nl = pd.read_csv(nl_api_url, parse_dates=["Award Date"])
    click.secho("Found {} National Lottery grants".format(len(nl)), fg="green")

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
            funding_oganization_type="Lottery Distributor",
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

    click.secho(
        "Excluding {} grants from National Lottery dataset".format(
            len(nl[nl["exclude"]])
        ),
        fg="green",
    )

    # Merge the National Lottery dataset into the main dataset.
    df = pd.concat(
        [
            df,
            nl[~nl["exclude"]].drop(columns=["exclude"]),
        ]
    )

    # Start with the `amount_awarded` column, which should be an integer.
    df["amount_awarded"] = df["amount_awarded"].astype(float)

    # Make sure award date is a date
    for field in ["award_date", "planned_dates_startDate", "planned_dates_endDate"]:
        df[field] = pd.to_datetime(df[field], utc=True, format="ISO8601").dt.date

    # set amount awarded GBP to same as amount awarded where currency is GBP
    df.loc[df["currency"] == "GBP", "amount_awarded_gbp"] = df.loc[
        df["currency"] == "GBP", "amount_awarded"
    ]

    results = defaultdict(lambda: 0)

    with transaction.atomic():
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
                results["CurrencyConverter created"] += 1
            else:
                results["CurrencyConverter found"] += 1

        with click.progressbar(
            df.replace({np.nan: None}).itertuples(),
            length=len(df),
            label="Saving Grant records",
        ) as bar:
            for grant in bar:
                grant_obj, created = Grant.objects.update_or_create(
                    grant_id=grant.Index,
                    defaults=dict(
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
                        recipient_type=grant.recipient_type,
                        funding_organisation_id=grant.funding_organization_id,
                        funding_organisation_name=grant.funding_organization_name,
                        funding_organisation_type=grant.funding_organization_type,
                        regrant_type_registered=grant.regrant_type,
                        location_scope=grant.location_scope,
                        grant_programme_title=grant.grant_programme_title,
                        publisher_prefix=grant.publisher_prefix,
                        publisher_name=grant.publisher_name,
                        license=grant.license,
                    ),
                )
                if grant_obj.inclusion == Grant.InclusionStatus.UNSURE:
                    if grant_obj.funding_organisation_type not in (
                        Grant.FunderType.CENTRAL_GOVERNMENT,
                        Grant.FunderType.DEVOLVED_GOVERNMENT,
                    ):
                        grant_obj.inclusion = Grant.InclusionStatus.INCLUDED
                        grant_obj.save()
                    elif grant_obj.recipient_organisation_id and (
                        grant_obj.recipient_organisation_id.startswith("GB-CHC-")
                        | grant_obj.recipient_organisation_id.startswith("GB-SC-")
                        | grant_obj.recipient_organisation_id.startswith("GB-NIC-")
                    ):
                        grant_obj.inclusion = Grant.InclusionStatus.INCLUDED
                        grant_obj.save()

                if created:
                    results["Grant created"] += 1
                else:
                    results["Grant updated"] += 1

    for key, value in results.items():
        click.secho("{}: {}".format(key, value), fg="green")
