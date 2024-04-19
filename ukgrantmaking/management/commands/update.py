import djclick as click
from django.db import transaction
from django.db.models import Case, F, Max, Sum, TextField, Value, When
from django.db.models.functions import (
    Cast,
    Coalesce,
    Concat,
    ExtractYear,
    NullIf,
    Right,
)

from ukgrantmaking.models import (
    DEFAULT_FINANCIAL_YEAR,
    FinancialYears,
    Funder,
    FunderYear,
)


@click.group(invoke_without_command=False)
def main():
    pass


@main.command()
@click.option("--financial-year", type=FinancialYears, default=DEFAULT_FINANCIAL_YEAR)
@click.option("--break-month", type=int, default=4)
def financial_year(financial_year=DEFAULT_FINANCIAL_YEAR, break_month=4):
    with transaction.atomic():
        click.secho("Updating financial years", fg="green")
        fy_update = 0
        fy_update += FunderYear.objects.filter(
            financial_year_end__month__gte=break_month
        ).update(
            financial_year=Concat(
                Cast(ExtractYear(F("financial_year_end")), output_field=TextField()),
                Value("-"),
                Right(
                    Cast(
                        ExtractYear(F("financial_year_end")) + 1,
                        output_field=TextField(),
                    ),
                    2,
                ),
            )
        )
        fy_update += FunderYear.objects.filter(
            financial_year_end__month__lt=break_month
        ).update(
            financial_year=Concat(
                Cast(
                    ExtractYear(F("financial_year_end")) - 1, output_field=TextField()
                ),
                Value("-"),
                Right(
                    Cast(
                        ExtractYear(F("financial_year_end")),
                        output_field=TextField(),
                    ),
                    2,
                ),
            )
        )
        click.secho(
            "Updated financial years for {:,.0f} records".format(fy_update), fg="green"
        )

        funder_updates = []
        click.secho("Updating funders latest grantmaking data", fg="green")
        query = Funder.objects.annotate(
            latest_id=Max(
                Case(
                    When(
                        funderyear__financial_year=financial_year,
                        then=F("funderyear__id"),
                    )
                )
            ),
            most_recent_grants=Sum(
                Case(
                    When(
                        funderyear__financial_year=financial_year,
                        then=Coalesce(
                            NullIf(F("funderyear__spending_grant_making"), Value(0)),
                            F("funderyear__spending_grant_making_institutions"),
                            F("funderyear__spending_charitable"),
                            F("funderyear__spending"),
                        ),
                    )
                )
            ),
        )
        with click.progressbar(query) as bar:
            for funder in bar:
                funder.latest_grantmaking = funder.most_recent_grants
                funder.latest_year_id = funder.latest_id
                funder_updates.append(funder)
        click.secho(
            "Updating {:,.0f} funders latest grantmaking data".format(
                len(funder_updates)
            ),
            fg="green",
        )
        Funder.objects.bulk_update(
            funder_updates, ["latest_grantmaking", "latest_year_id"]
        )
