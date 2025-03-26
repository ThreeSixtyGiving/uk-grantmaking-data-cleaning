import djclick as click
import pandas as pd

from ukgrantmaking.models.funder import Funder
from ukgrantmaking.models.funder_year import FunderYear


@click.command(deprecated=True)
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
                and not funder_year.spending_grant_making_institutions_main_manual
            ):
                funder_year.spending_grant_making_institutions_main_manual = (
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
