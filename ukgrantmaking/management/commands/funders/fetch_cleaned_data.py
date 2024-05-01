from glob import glob

import djclick as click
import numpy as np
import pandas as pd

from ukgrantmaking.models import FunderYear


@click.command()
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
