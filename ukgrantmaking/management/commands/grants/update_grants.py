import logging
from collections import defaultdict
from datetime import timedelta

import djclick as click
from django.db import transaction
from django.db.models import F, Sum

from ukgrantmaking.models.financial_years import FinancialYear, FinancialYearStatus
from ukgrantmaking.models.funder import Funder
from ukgrantmaking.models.funder_financial_year import FunderFinancialYear
from ukgrantmaking.models.funder_year import FunderYear
from ukgrantmaking.models.grant import CurrencyConverter, Grant

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@click.command()
@click.option("--financial-year", type=str, required=False)
@click.argument("funder_ids", type=str, required=False, nargs=-1)
def grants(financial_year, funder_ids):
    with transaction.atomic():
        logger.info("Updating amount awarded not in GBP")
        currencies = {
            (currency.currency, currency.date): currency.rate
            for currency in CurrencyConverter.objects.filter(rate__isnull=False)
        }
        currency_results = defaultdict(lambda: 0)
        for currency, rate in currencies.items():
            result = Grant.objects.filter(
                currency=currency[0],
                award_date=currency[1],
            ).update(amount_awarded_GBP=F("amount_awarded") * rate)
            currency_results[currency[0]] += result

        for key, value in currency_results.items():
            logger.info(f"   - {key}: {value:,.0f} grants updated")

        logger.info("Match funders to funder records")
        if not funder_ids:
            funder_ids = Funder.objects.values_list("org_id", flat=True)
        result = Grant.objects.filter(
            funder_id__isnull=True,
            funding_organisation_id__in=funder_ids,
        ).update(funder_id=F("funding_organisation_id"))
        logger.info(f"{result} grants updated with funder ID")

        missing_funder_ids = Grant.objects.filter(funder_id__isnull=True).count()
        logger.warning(f"{missing_funder_ids} grants missing funder ID")
        for funder in (
            Grant.objects.filter(funder_id__isnull=True)
            .values_list("funding_organisation_id", "funding_organisation_name")
            .distinct()
        ):
            logger.warning(f"   {funder[0]} - {funder[1]}")

        # update financial years on all grants
        for fy in FinancialYear.objects.all():
            Grant.objects.filter(
                financial_year__isnull=True,
                award_date__gte=fy.grants_start_date,
                award_date__lte=fy.grants_end_date,
            ).update(financial_year=fy)

        # update funder years
        logger.info("Updating funder years")
        if funder_ids:
            funders = (
                Grant.objects.filter(funder_id__in=funder_ids)
                .values_list("funder_id", flat=True)
                .distinct()
            )
        else:
            funders = (
                Grant.objects.filter(funder_id__isnull=False)
                .values_list("funder_id", flat=True)
                .distinct()
            )
        if financial_year:
            financial_years = FinancialYear.objects.filter(fy=financial_year)
        else:
            financial_years = FinancialYear.objects.filter(
                current=True, status=FinancialYearStatus.OPEN
            )
        bulk_update = []
        results = defaultdict(lambda: 0)
        for funder_id in funders:
            try:
                funder = Funder.objects.get(org_id=funder_id)
            except Funder.DoesNotExist:
                logger.info(f"Funder {funder_id} not found")
                continue
            for year in financial_years:
                funder_years = FunderYear.objects.filter(
                    funder_financial_year__funder=funder,
                    funder_financial_year__financial_year=year,
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
                                funder_id=funder.org_id,
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
                        grant_amounts = {
                            "Organisation": 0,
                            "Individual": 0,
                        }
                        changed = False
                        for grant_amount in grants_amount_by_recipient:
                            if grant_amount["recipient_type"] != "Individual":
                                grant_amounts["Organisation"] += grant_amount[
                                    "grants_amount"
                                ]
                                changed = True
                            if grant_amount["recipient_type"] == "Individual":
                                grant_amounts["Individual"] += grant_amount[
                                    "grants_amount"
                                ]
                                changed = True
                        if changed:
                            funder_year.spending_grant_making_institutions_main_360Giving = grant_amounts[
                                "Organisation"
                            ]
                            funder_year.spending_grant_making_individuals_360Giving = (
                                grant_amounts["Individual"]
                            )
                            logger.info(
                                f"Updating {funder.name} [{funder.org_id}] {funder_year.financial_year_end}",
                            )
                            results["Funder years updated"] += 1
                            bulk_update.append(funder_year)

                # otherwise check for grants data and add it if it exists
                else:
                    grants_amount_by_recipient = (
                        Grant.objects.filter(
                            funder_id=funder.org_id,
                            award_date__lte=year.grants_end_date,
                            award_date__gte=year.grants_start_date,
                            inclusion__in=[
                                Grant.InclusionStatus.INCLUDED,
                                Grant.InclusionStatus.UNSURE,
                            ],
                        )
                        .values("recipient_type")
                        .annotate(grants_amount=Sum("amount_awarded_GBP"))
                    )
                    if grants_amount_by_recipient:
                        funder_financial_year = (
                            FunderFinancialYear.objects.get_or_create(
                                funder=funder, financial_year=year
                            )[0]
                        )
                        funder_year = FunderYear(
                            funder_financial_year=funder_financial_year,
                            financial_year_start=year.grants_start_date,
                            financial_year_end=year.grants_end_date,
                        )
                        logger.info(
                            f"Creating {funder_financial_year.funder} {funder_year.financial_year_end}",
                        )
                        grant_amounts = {
                            "Organisation": 0,
                            "Individual": 0,
                        }
                        changed = False
                        for grant_amount in grants_amount_by_recipient:
                            if grant_amount["recipient_type"] != "Individual":
                                grant_amounts["Organisation"] += grant_amount[
                                    "grants_amount"
                                ]
                                changed = True
                            if grant_amount["recipient_type"] == "Individual":
                                grant_amounts["Individual"] += grant_amount[
                                    "grants_amount"
                                ]
                                changed = True
                        if changed:
                            funder_year.spending_grant_making_institutions_main_360Giving = grant_amounts[
                                "Organisation"
                            ]
                            funder_year.spending_grant_making_individuals_360Giving = (
                                grant_amounts["Individual"]
                            )
                            logger.info(
                                f"Updating {funder.name} [{funder.org_id}] {funder_year.financial_year_end}",
                            )
                            results["Funder years created"] += 1
                            funder_year.save()

        updated = FunderYear.objects.bulk_update(
            bulk_update,
            [
                "spending_grant_making_institutions_main_360Giving",
                "spending_grant_making_individuals_360Giving",
            ],
        )

        for key, value in results.items():
            logger.info(f"{value}: {key}")
        logger.info(f"Updated {updated} funder years")
