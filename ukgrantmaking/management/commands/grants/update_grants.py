import djclick as click
from django.db import transaction
from django.db.models import F

from ukgrantmaking.models import (
    CurrencyConverter,
    Grant,
)
from ukgrantmaking.models.funder import Funder


@click.command()
def grants():
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
