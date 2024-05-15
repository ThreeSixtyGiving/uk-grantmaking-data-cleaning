import djclick as click
import numpy as np
import pandas as pd
from django.db import transaction

from ukgrantmaking.models import Funder, FunderYear
from ukgrantmaking.utils.text import to_titlecase


@click.command()
@click.argument("db_con", envvar="FTC_DB_URL")
def ftc(db_con):
    # get list of org IDs
    org_ids = tuple(Funder.objects.all().values_list("org_id", flat=True))

    # get updated names and date of registration from FTC
    org_records = pd.read_sql(
        """
        SELECT org_id,
            name,
            "dateRegistered",
            "dateRemoved",
            "active"
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
                funder.date_of_removal = org_record.dateRemoved
                funder.active = org_record.active
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
