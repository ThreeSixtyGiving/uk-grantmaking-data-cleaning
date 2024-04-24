from glob import glob

import djclick as click
import numpy as np
import pandas as pd
from django.db import transaction
from openpyxl import load_workbook

from ukgrantmaking.models import Funder, FunderTag, FunderYear
from ukgrantmaking.utils.text import to_titlecase

TAG_LOOKUP = {
    "foundation_giving_trends": "Foundation Giving Trends",
    "360Giving_publisher": "360Giving Publisher",
    "snapshot_2023": "Snapshot 2023",
    "external: ACF_Current": "ACF Current",
    "external: ACF_Previous": "ACF Previous",
    "external: ACO": "ACO",
    "external: Community_Foundation": "Community Foundation",
    "external: Companies & Guilds": "Companies & Guilds",
    "external: Funders Forum for NI": "Funders Forum for NI",
    "external: Living Wage Funder": "Living Wage Funder",
    "external: London Funder": "London Funder",
    "external: UKCF": "UKCF",
    "dsc": "DSC",
    "ccew": "CCEW",
    "oscr": "OSCR",
    "ccni": "CCNI",
}


@click.group(invoke_without_command=False)
def main():
    pass


@main.command()
@click.argument("file")
def master_list(file):
    click.secho("Opening {}".format(file), fg="green")

    wb = load_workbook(filename=file)

    funder_tags = {tag.tag: tag for tag in FunderTag.objects.all()}

    records = {
        "created": 0,
        "updated": 0,
    }

    with transaction.atomic():
        for sheet in wb:
            # iterate rows
            for table_name, table_range in sheet.tables.items():
                click.secho(
                    "Sheet: {} | Table: {}".format(sheet.title, table_name), fg="yellow"
                )

                header_row = None
                for row in sheet[table_range]:
                    if header_row is None:
                        header_row = [cell.value for cell in row]
                        continue
                    record = dict(zip(header_row, [cell.value for cell in row]))

                    # create or update Funder
                    funder, created = Funder.objects.get_or_create(
                        org_id=record["org_id"],
                        defaults={
                            "name_registered": record["name"],
                            "charity_number": record["charityNumber"],
                            "segment": record.get("segment_checked", record["segment"]),
                            "included": (
                                record["inclusion"] in ("non_charities", "included")
                            ),
                            "makes_grants_to_individuals": (
                                record["grants_to_individuals"] is not None
                            ),
                            "date_of_registration": record["dateRegistered"],
                            "activities": record["description"],
                            "website": record["url"],
                        },
                    )
                    if created:
                        records["created"] += 1
                        for field, value in TAG_LOOKUP.items():
                            if record.get(field):
                                funder.tags.add(funder_tags[value])
                    else:
                        records["updated"] += 1

    click.secho(
        "Created: {created}, Existing: {updated}".format(**records),
        fg="green",
    )


@main.command()
@click.argument("db_con", envvar="FTC_DB_URL")
def ftc(db_con):
    # get list of org IDs
    org_ids = tuple(Funder.objects.all().values_list("org_id", flat=True))

    # get updated names and date of registration from FTC
    org_records = pd.read_sql(
        """
        SELECT org_id,
            name,
            "dateRegistered"
        FROM ftc_organisation
        WHERE org_id IN %(org_id)s
        """,
        params={"org_id": org_ids},
        con=db_con,
    )
    org_cache = {}
    with transaction.atomic():
        with click.progressbar(
            org_records.itertuples(),
            length=len(org_records),
            label="Updating organisation data",
        ) as bar:
            for org_record in bar:
                funder = Funder.objects.get(org_id=org_record.org_id)
                org_cache[funder.org_id] = funder
                funder.name_registered = to_titlecase(org_record.name)
                funder.date_of_registration = org_record.dateRegistered
                funder.save()

    finance_records = pd.read_sql(
        """
        SELECT charity_id AS org_id,
            fyend AS financial_year_end,
            fystart AS financial_year_start,
            income,
            spending,
            exp_charble AS spending_charitable,
            exp_grant AS spending_grant_making_institutions,
            funds_total AS total_net_assets,
            funds_total AS funds,
            funds_end AS funds_endowment,
            funds_restrict AS funds_restricted,
            funds_unrestrict AS funds_unrestricted,
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
            label="Updating organisation finances",
        ) as bar:
            for financial_record in bar:
                if financial_record.org_id not in org_cache:
                    funder = Funder.objects.get(org_id=financial_record.org_id)
                    org_cache[financial_record.org_id] = funder
                else:
                    funder = org_cache[financial_record.org_id]
                funder_year, created = FunderYear.objects.update_or_create(
                    funder=funder,
                    financial_year_end=financial_record.financial_year_end,
                    defaults=dict(
                        financial_year_start=financial_record.financial_year_start,
                        income_registered=financial_record.income,
                        spending_registered=financial_record.spending,
                        spending_charitable_registered=financial_record.spending_charitable,
                        spending_grant_making_institutions_registered=financial_record.spending_grant_making_institutions,
                        total_net_assets_registered=financial_record.total_net_assets,
                        funds_registered=financial_record.funds,
                        funds_endowment_registered=financial_record.funds_endowment,
                        funds_restricted_registered=financial_record.funds_restricted,
                        funds_unrestricted_registered=financial_record.funds_unrestricted,
                        employees_registered=financial_record.employees,
                    ),
                )


@main.command()
@click.argument("files", nargs=-1)
def cleaned_data(files):
    index_columns = ["org_id", "fyend"]
    columns_to_use = [
        "checked_status",
        "checked_by",
        "checked_time",
        "notes",
        "income_checked",
        "spending_checked",
        "exp_charble_checked",
        "spending_on_grants_to_individuals",
        "spending_on_grants_to_institutions",
        "total_assets_checked",
        "funds_end_checked",
        "funds_restrict_checked",
        "funds_unrestrict_checked",
        "funds_total_checked",
        "employees_checked",
    ]

    checked_data = []

    for globbable in files:
        for file in glob(globbable):
            click.secho("Opening {}".format(file), fg="green")
            df = (
                pd.read_excel(file)[index_columns + columns_to_use]
                .dropna(
                    subset=index_columns,
                    how="any",
                )
                .dropna(
                    subset=columns_to_use,
                    how="all",
                )
            )
            checked_data.append(df)
            click.secho("Found {} records in {}".format(len(df), file), fg="green")

    checked_data = pd.concat(checked_data, ignore_index=True)
    click.secho("Found {} records total".format(len(checked_data)), fg="green")

    records = {
        "Created": 0,
        "Updated": 0,
    }
    for record in checked_data.replace({np.nan: None}).itertuples():
        funder, created = FunderYear.objects.update_or_create(
            funder_id=record.org_id,
            financial_year_end=record.fyend,
            defaults=dict(
                income_manual=record.income_checked,
                spending_manual=record.spending_checked,
                spending_charitable_manual=record.exp_charble_checked,
                spending_grant_making_individuals_manual=record.spending_on_grants_to_individuals,
                spending_grant_making_institutions_manual=record.spending_on_grants_to_institutions,
                total_net_assets_manual=record.total_assets_checked,
                funds_manual=record.funds_end_checked,
                funds_endowment_manual=record.funds_end_checked,
                funds_restricted_manual=record.funds_restrict_checked,
                funds_unrestricted_manual=record.funds_unrestrict_checked,
                employees_manual=record.employees_checked,
                checked_by=record.checked_by,
                notes=record.notes,
            ),
        )
        records["Created" if created else "Updated"] += 1

    for key, value in records.items():
        click.secho("{}: {}".format(key, value), fg="green")


@main.command()
@click.argument("file")
@click.option("--orgid-column", default="org_id")
@click.option("--tag-column", default="tag")
@click.option("--tag", default=None)
@click.option("--name-column", default="name")
def tags(file, orgid_column, tag_column, tag, name_column):
    click.secho("Opening {}".format(file), fg="green")
    df = pd.read_excel(file)

    if not tag and tag_column not in df.columns:
        raise click.ClickException("Tag column not found in file and no tag provided")

    funder_tags = {}
    if tag_column in df.columns:
        for tag_record in df[tag_column].unique():
            tag_record = tag_record.strip()
            funder_tag, tag_created = FunderTag.objects.get_or_create(
                tag=tag_record,
            )
            funder_tags[tag_record] = funder_tag
    if tag:
        tag = tag.strip()
        funder_tags[tag], tag_created = FunderTag.objects.get_or_create(
            tag=tag,
        )

    records = {
        "Funder created": 0,
        "Funder found": 0,
    }
    for index, record in df.replace({np.nan: None}).iterrows():
        # skip if no orgid
        if not getattr(record, orgid_column, None):
            continue

        defaults = {}
        if hasattr(record, name_column):
            defaults["name_registered"] = getattr(record, name_column)
        funder, created = Funder.objects.get_or_create(
            org_id=getattr(record, orgid_column),
            defaults=defaults,
        )
        if tag:
            funder.tags.add(funder_tags[tag])
        if isinstance(getattr(record, tag_column, None), str):
            tag_value = getattr(record, tag_column).strip()
            funder.tags.add(funder_tags[tag_value])
        records["Funder created" if created else "Funder found"] += 1

    for key, value in records.items():
        click.secho("{}: {}".format(key, value), fg="green")


@main.command()
@click.argument("file")
def fgt(file):
    click.secho("Opening {}".format(file), fg="green")
    df = pd.read_excel(file)
    with click.progressbar(
        df.iterrows(),
        length=len(df),
        label="Updating finances from FGT",
    ) as bar:
        for index, row in bar:
            try:
                funder_year = FunderYear.objects.get(
                    funder_id=row["Org-id"],
                    financial_year_end=row["Financial Year"],
                )
            except FunderYear.DoesNotExist:
                try:
                    funder_year = FunderYear.objects.get(
                        funder_id=row["Org-id"],
                        financial_year_end__month=row["Financial Year"].month,
                        financial_year_end__year=row["Financial Year"].year,
                    )
                except FunderYear.DoesNotExist:
                    try:
                        funder_year = FunderYear.objects.get(
                            funder_id=row["Org-id"],
                            financial_year_end__year=row["Financial Year"].year,
                        )
                    except FunderYear.DoesNotExist:
                        funder, funder_created = Funder.objects.get_or_create(
                            org_id=row["Org-id"],
                            defaults={"name_registered": row["Name"]},
                        )
                        if funder_created:
                            click.secho(
                                "Created Funder {} ({})".format(
                                    funder.name_registered, funder.org_id
                                ),
                                fg="green",
                            )
                        funder_year = FunderYear(
                            funder_id=row["Org-id"],
                            financial_year_end=row["Financial Year"],
                            notes="Added from Foundation Giving Trends data",
                        )

            if (
                not pd.isna(row["Giving £m"])
                and not funder_year.spending_grant_making_institutions_manual
            ):
                funder_year.spending_grant_making_institutions_manual = (
                    row["Giving £m"] * 1_000_000
                )

            if (
                not pd.isna(row["Assets £m"])
                and not funder_year.total_net_assets_manual
            ):
                funder_year.total_net_assets_manual = row["Assets £m"] * 1_000_000

            if not pd.isna(row["Notes"]) and not funder_year.notes:
                funder_year.notes = row["Notes"]

            funder_year.save()
