import logging

import djclick as click
import numpy as np
import pandas as pd
from django.db import connection, transaction

from ukgrantmaking.management.commands.funders.update_financial_year import (
    SQL_QUERIES,
    format_query,
)
from ukgrantmaking.models.financial_years import FinancialYear
from ukgrantmaking.models.funder import Funder
from ukgrantmaking.models.funder_year import FunderFinancialYear, FunderYear
from ukgrantmaking.utils import do_batched_update
from ukgrantmaking.utils.text import to_titlecase

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@click.command()
@click.argument("db_con", envvar="FTC_DB_URL")
@click.option("--do-funders/--skip-funders", is_flag=True, default=True)
@click.option("--do-financial/--skip-financial", is_flag=True, default=True)
def ftc(db_con, do_funders, do_financial):
    with transaction.atomic(), connection.cursor() as cursor:
        # get list of org IDs
        org_ids = tuple(Funder.objects.all().values_list("org_id", flat=True))

        if do_funders:
            # get updated names and date of registration from FTC
            logging.info("Fetching organisations from FTC")
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
            logger.info(f"Fetched {len(org_records):,.0f} organisations from FTC")
            with click.progressbar(
                org_records.itertuples(),
                length=len(org_records),
                label="Updating organisation data",
            ) as bar:
                for org_record in bar:
                    funder = Funder.objects.get(org_id=org_record.org_id)
                    funder.name_registered = to_titlecase(org_record.name)
                    funder.date_of_registration = org_record.dateRegistered
                    funder.date_of_removal = org_record.dateRemoved
                    funder.active = org_record.active
                    funder.save()

        if not do_financial:
            return

        # get all financial years
        financial_years = pd.DataFrame(FinancialYear.objects.all().values())

        # check that we've got a financial year for every funder
        query_keys = [
            "Ensure every funder has a funder financial year for the current financial year",
        ]
        queries = {query_name: SQL_QUERIES[query_name] for query_name in query_keys}
        for query_name, query in queries.items():
            logger.info(f"[Query] Started:  {query_name}")
            cursor.execute(format_query(query))
            logger.info(f"[Query] Completed: {query_name}")
            logger.info(f"[Query] Rows affected: {cursor.rowcount:,.0f}")

        # get all funder years
        logger.info("Fetching funder financial years from DB")
        funder_financial_years = (
            pd.DataFrame(
                FunderFinancialYear.objects.values(
                    "id",
                    "funder_id",
                    "financial_year__fy",
                )
            )
            .set_index(["funder_id", "financial_year__fy"])["id"]
            .rename("funder_financial_year_id")
        )
        logger.info(
            f"Fetched {len(funder_financial_years):,.0f} financial years from DB"
        )

        # get successor lookups
        logger.info("Fetching successor lookups from DB")
        successor_lookups = dict(
            Funder.objects.filter(successor__isnull=False).values_list(
                "org_id", "successor_id"
            )
        )
        logger.info(f"Fetched {len(successor_lookups):,.0f} successor lookups from DB")

        logger.info("Fetching financial records from FTC")
        finance_records = pd.read_sql(
            """
            SELECT charity_id AS org_id,
                fyend AS financial_year_end,
                fystart AS financial_year_start,
                income,
                inc_invest AS income_investment,
                spending,
                exp_invest AS spending_investment,
                exp_charble AS spending_charitable,
                exp_grant AS spending_grant_making_institutions_unknown,
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
        logger.info(f"Fetched {len(finance_records):,.0f} financial records from FTC")

        # replace org IDs with successor IDs
        finance_records["original_org_id"] = finance_records["org_id"]
        finance_records["org_id"] = finance_records["org_id"].replace(successor_lookups)

        finance_records["fy"] = None
        for fy in financial_years.itertuples():
            finance_records.loc[
                (finance_records.financial_year_end >= fy.funders_start_date)
                & (finance_records.financial_year_end <= fy.funders_end_date),
                "fy",
            ] = fy.fy

        finance_records = finance_records.join(
            funder_financial_years,
            on=["org_id", "fy"],
            how="left",
        ).join(
            funder_financial_years.rename("original_funder_financial_year_id"),
            on=["org_id_original", "fy"],
            how="left",
        )
        finance_records.loc[
            finance_records["funder_financial_year_id"]
            == finance_records["original_funder_financial_year_id"],
            "original_funder_financial_year_id",
        ] = None

        no_fy = finance_records[finance_records.funder_financial_year_id.isnull()]
        logger.info(
            f"Found {len(no_fy):,.0f} records that didn't match a financial year"
        )
        for fy, count in no_fy["fy"].value_counts().items():
            logger.info(f"  {fy}: {count:,.0f}")

        finance_records = finance_records[
            ~finance_records.funder_financial_year_id.isnull()
        ]

        with click.progressbar(
            finance_records.replace({np.nan: None}).itertuples(),
            length=len(finance_records),
            label="Updating organisation finances",
        ) as bar:

            def iterate_fy():
                for financial_record in bar:
                    yield dict(
                        financial_year_id=financial_record.funder_financial_year_id,
                        financial_year_end=financial_record.financial_year_end,
                        financial_year_start=financial_record.financial_year_start,
                        income_registered=financial_record.income,
                        income_investment_registered=financial_record.income_investment,
                        spending_registered=financial_record.spending,
                        spending_investment_registered=financial_record.spending_investment,
                        spending_charitable_registered=financial_record.spending_charitable,
                        spending_grant_making_institutions_unknown_registered=financial_record.spending_grant_making_institutions_unknown,
                        total_net_assets_registered=financial_record.total_net_assets,
                        funds_registered=financial_record.funds,
                        funds_endowment_registered=financial_record.funds_endowment,
                        funds_restricted_registered=financial_record.funds_restricted,
                        funds_unrestricted_registered=financial_record.funds_unrestricted,
                        employees_registered=financial_record.employees,
                    )

            do_batched_update(
                FunderYear,
                iterate_fy,
                unique_fields=[
                    "financial_year_id",
                    "financial_year_end",
                ],
                update_fields=[
                    "financial_year_start",
                    "income_registered",
                    "income_investment_registered",
                    "spending_registered",
                    "spending_investment_registered",
                    "spending_charitable_registered",
                    "spending_grant_making_institutions_unknown_registered",
                    "total_net_assets_registered",
                    "funds_registered",
                    "funds_endowment_registered",
                    "funds_restricted_registered",
                    "funds_unrestricted_registered",
                    "employees_registered",
                ],
            )
