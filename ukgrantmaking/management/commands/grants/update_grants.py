from collections import defaultdict
from datetime import timedelta

import djclick as click
from caradoc import FinancialYear
from django.core.management import call_command
from django.db import transaction
from django.db.models import F, Sum

from ukgrantmaking.models import (
    CurrencyConverter,
    Grant,
)
from ukgrantmaking.models.funder import Funder
from ukgrantmaking.models.funder_year import FinancialYears, FunderYear


@click.command()
def grants():
    call_command("update", "financial-year")
    with transaction.atomic():
        click.secho("Updating amount awarded in GBP", fg="green")
        currencies = {
            (currency.currency, currency.date): currency.rate
            for currency in CurrencyConverter.objects.filter(rate__isnull=False)
        }
        for currency, rate in currencies.items():
            result = Grant.objects.filter(
                currency=currency[0],
                award_date=currency[1],
            ).update(amount_awarded_GBP=F("amount_awarded") * rate)
            click.secho(
                f"{result} grants updated [{currency[0]} - {currency[1]:%Y-%m-%d} - {rate}]",
                fg="green",
            )

        click.secho("Match funders to funder records", fg="green")
        funder_ids = Funder.objects.values_list("org_id", flat=True)
        result = Grant.objects.filter(
            funder_id__isnull=True,
            funding_organisation_id__in=funder_ids,
        ).update(funder_id=F("funding_organisation_id"))
        click.secho(f"{result} grants updated with funder ID", fg="green")

        missing_funder_ids = Grant.objects.filter(funder_id__isnull=True).count()
        click.secho(f"{missing_funder_ids} grants missing funder ID", fg="red")
        for funder in (
            Grant.objects.filter(funder_id__isnull=True)
            .values_list("funding_organisation_id", "funding_organisation_name")
            .distinct()
        ):
            click.secho(f"   {funder[0]} - {funder[1]}", fg="red")

        # update funder years
        click.secho("Updating funder years", fg="green")
        funders = (
            Grant.objects.filter(funder_id__isnull=False)
            .values_list("funder_id", flat=True)
            .distinct()
        )
        bulk_update = []
        results = defaultdict(lambda: 0)
        for funder_id in funders:
            try:
                funder = Funder.objects.get(org_id=funder_id)
            except Funder.DoesNotExist:
                click.secho(f"Funder {funder_id} not found", fg="red")
                continue
            for year, _ in FinancialYears.choices:
                fy = FinancialYear(year)
                funder_years = FunderYear.objects.filter(
                    funder=funder,
                    financial_year=year,
                )

                # if we've got existing data then use it
                if funder_years:
                    for funder_year in funder_years:
                        financial_year_start = funder_year.financial_year_start
                        if financial_year_start is None:
                            financial_year_start = (
                                funder_year.financial_year_end - timedelta(days=365)
                            )
                        grants_amount_by_recipient = (
                            Grant.objects.filter(
                                funder_id=funder_year.funder_id,
                                award_date__lte=funder_year.financial_year_end,
                                award_date__gte=financial_year_start,
                                inclusion__in=[
                                    Grant.InclusionStatus.INCLUDED,
                                    Grant.InclusionStatus.UNSURE,
                                ],
                            )
                            .values("recipient_type")
                            .annotate(grants_amount=Sum("amount_awarded_GBP"))
                        )
                        for grant_amount in grants_amount_by_recipient:
                            changed = False
                            if grant_amount["recipient_type"] == "Organisation":
                                funder_year.spending_grant_making_institutions_360Giving = grant_amount[
                                    "grants_amount"
                                ]
                                changed = True
                            if grant_amount["recipient_type"] == "Individual":
                                funder_year.spending_grant_making_individuals_360Giving = grant_amount[
                                    "grants_amount"
                                ]
                                changed = True
                            if changed:
                                click.secho(
                                    f"Updating {funder_year.funder} {funder_year.financial_year_end}",
                                    fg="green",
                                )
                                results["Funder years updated"] += 1
                                bulk_update.append(funder_year)

                # otherwise check for grants data and add it if it exists
                else:
                    grants_amount_by_recipient = (
                        Grant.objects.filter(
                            funder_id=funder.org_id,
                            award_date__lte=fy.end_date,
                            award_date__gte=fy.start_date,
                            inclusion__in=[
                                Grant.InclusionStatus.INCLUDED,
                                Grant.InclusionStatus.UNSURE,
                            ],
                        )
                        .values("recipient_type")
                        .annotate(grants_amount=Sum("amount_awarded_GBP"))
                    )
                    if grants_amount_by_recipient:
                        funder_year = FunderYear(
                            funder=funder,
                            financial_year=year,
                            financial_year_start=fy.start_date,
                            financial_year_end=fy.end_date,
                        )
                        click.secho(
                            f"Creating {funder_year.funder} {funder_year.financial_year_end}",
                            fg="green",
                        )
                        for grant_amount in grants_amount_by_recipient:
                            changed = False
                            if grant_amount["recipient_type"] == "Organisation":
                                funder_year.spending_grant_making_institutions_360Giving = grant_amount[
                                    "grants_amount"
                                ]
                                changed = True
                            if grant_amount["recipient_type"] == "Individual":
                                funder_year.spending_grant_making_individuals_360Giving = grant_amount[
                                    "grants_amount"
                                ]
                                changed = True
                            if changed:
                                results["Funder years created"] += 1
                                funder_year.save()

        updated = FunderYear.objects.bulk_update(
            bulk_update,
            [
                "spending_grant_making_institutions_360Giving",
                "spending_grant_making_individuals_360Giving",
            ],
        )

        for key, value in results.items():
            click.secho(f"{value}: {key}", fg="green")
        click.secho(f"Updated {updated} funder years", fg="green")
