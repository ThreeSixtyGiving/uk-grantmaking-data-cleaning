import logging

import djclick as click
from django.apps import apps
from django.db import connection, transaction

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SQL_QUERIES = {
    "Ensure every funder has a funder financial year for the current financial year": """
    WITH fy AS (
        SELECT *
        FROM {ukgrantmaking_financialyear}
        WHERE "current" OR status != 'Future'
        ORDER BY fy DESC
        LIMIT 5
    )
    INSERT INTO
        {ukgrantmaking_funderfinancialyear} (
            financial_year_id,
            funder_id,
            segment,
            included,
            makes_grants_to_individuals
        )
    SELECT
        fy.fy AS financial_year_id,
        f.org_id AS funder_id,
        f.segment AS segment,
        f.included AS included,
        f.makes_grants_to_individuals AS makes_grants_to_individuals
    FROM
        {ukgrantmaking_funder} f, fy
    WHERE f.active = TRUE
        OR f.active IS NULL
    ON CONFLICT (financial_year_id, funder_id) DO NOTHING
    """,
    "Update tags": """
    INSERT INTO {ukgrantmaking_funder_tags} (funder_id, fundertag_id)
    SELECT org_id AS funder_id,
        CASE WHEN org_id ILIKE 'GB-CHC-%%' THEN 'ccew'
            WHEN org_id ILIKE 'GB-SC-%%' THEN 'oscr'
            WHEN org_id ILIKE 'GB-NIC-%%' THEN 'ccni'
            ELSE NULL END AS "fundertag_id"
    FROM {ukgrantmaking_funder}
    WHERE org_id ~* 'GB-(CHC|NIC|SC)-*'
    ON CONFLICT (funder_id, fundertag_id) DO NOTHING
    """,
    "Set the current year to the correct year": """
    WITH current_fy AS (
        SELECT *
        FROM {ukgrantmaking_financialyear}
        WHERE "current" = TRUE
    )
    UPDATE {ukgrantmaking_funder}
    SET current_year_id = ffy.id 
    FROM {ukgrantmaking_funderfinancialyear} ffy
        INNER JOIN current_fy
            ON ffy.financial_year_id = current_fy.fy
    WHERE ffy.funder_id = {ukgrantmaking_funder}.org_id
    """,
    "Set the latest year to the correct year": """
    WITH current_fys AS (
        SELECT *
        FROM {ukgrantmaking_financialyear}
        WHERE status != 'Future'
        ORDER BY fy DESC
    ),
    funder_year_count AS (
        SELECT funder_financial_year_id,
            COUNT(*) AS funder_years
        FROM {ukgrantmaking_funderyear} fy
        GROUP BY 1
    ),
    latest_ffy AS (
        SELECT DISTINCT ON (funder_id)
            funder_id,
            ffy.id,
            ffy.financial_year_id
        FROM {ukgrantmaking_funderfinancialyear} ffy
            INNER JOIN current_fys
                ON ffy.financial_year_id = current_fys.fy
            LEFT OUTER JOIN funder_year_count
                ON ffy.id = funder_year_count.funder_financial_year_id
        WHERE funder_year_count.funder_years > 0
        ORDER BY funder_id ASC, current_fys.fy DESC
    )
    UPDATE {ukgrantmaking_funder}
    SET latest_year_id = latest_ffy.id 
    FROM latest_ffy
    WHERE latest_ffy.funder_id = {ukgrantmaking_funder}.org_id
    """,
    "Recalculate aggregate values for funder financial years": """
    WITH fy AS (
        SELECT
            *,
            case when (
                funds_endowment IS NOT NULL OR  
                funds_restricted IS NOT NULL OR  
                funds_unrestricted IS NOT NULL
            ) then (
                coalesce(funds_endowment, 0) + 
                coalesce(funds_restricted, 0) + 
                coalesce(funds_unrestricted, 0)
            ) else null end as funds_calculated,
            case when (
                employees_permanent IS NOT NULL OR  
                employees_fixedterm IS NOT NULL OR  
                employees_selfemployed IS NOT NULL
            ) then (
                coalesce(employees_permanent, 0) + 
                coalesce(employees_fixedterm, 0) + 
                coalesce(employees_selfemployed, 0)
            ) else null end as employees_calculated
        FROM
            {ukgrantmaking_funderyear} fy
        ORDER BY
            financial_year_end DESC
    ),
    latest_fields AS (
        SELECT
            DISTINCT ON (funder_financial_year_id) funder_financial_year_id,
            coalesce(total_net_assets, funds_calculated) AS total_net_assets,
            coalesce(funds, funds_calculated) AS funds,
            funds_endowment,
            funds_restricted,
            funds_unrestricted,
            coalesce(employees, employees_calculated) AS employees,
            employees_permanent,
            employees_fixedterm,
            employees_selfemployed
        FROM
            fy
    ),
    summed_fields AS (
        SELECT
            funder_financial_year_id,
            sum(income) AS income,
            sum(income_investment) AS income_investment,
            sum(spending) AS spending,
            sum(spending_investment) AS spending_investment,
            sum(spending_charitable) AS spending_charitable,
            sum(spending_grant_making) AS spending_grant_making,
            sum(spending_grant_making_individuals) AS spending_grant_making_individuals,
            sum(spending_grant_making_institutions_charitable) AS spending_grant_making_institutions_charitable,
            sum(spending_grant_making_institutions_noncharitable) AS spending_grant_making_institutions_noncharitable,
            sum(spending_grant_making_institutions_unknown) AS spending_grant_making_institutions_unknown,
            sum(spending_grant_making_institutions_main) AS spending_grant_making_institutions_main,
            sum(spending_grant_making_institutions) AS spending_grant_making_institutions
        FROM
            fy
        GROUP BY
            1
    )
    UPDATE
        {ukgrantmaking_funderfinancialyear}
    SET
        income = summed_fields.income,
        income_investment = summed_fields.income_investment,
        spending = summed_fields.spending,
        spending_investment = summed_fields.spending_investment,
        spending_charitable = summed_fields.spending_charitable,
        spending_grant_making = summed_fields.spending_grant_making,
        spending_grant_making_individuals = summed_fields.spending_grant_making_individuals,
        spending_grant_making_institutions_charitable = summed_fields.spending_grant_making_institutions_charitable,
        spending_grant_making_institutions_noncharitable = summed_fields.spending_grant_making_institutions_noncharitable,
        spending_grant_making_institutions_unknown = summed_fields.spending_grant_making_institutions_unknown,
        spending_grant_making_institutions_main = summed_fields.spending_grant_making_institutions_main,
        spending_grant_making_institutions = summed_fields.spending_grant_making_institutions,
        total_net_assets = latest_fields.total_net_assets,
        funds = latest_fields.funds,
        funds_endowment = latest_fields.funds_endowment,
        funds_restricted = latest_fields.funds_restricted,
        funds_unrestricted = latest_fields.funds_unrestricted,
        employees = latest_fields.employees,
        employees_permanent = latest_fields.employees_permanent,
        employees_fixedterm = latest_fields.employees_fixedterm,
        employees_selfemployed = latest_fields.employees_selfemployed
    FROM
        latest_fields,
        summed_fields
    WHERE
        {ukgrantmaking_funderfinancialyear}.id = latest_fields.funder_financial_year_id
        AND {ukgrantmaking_funderfinancialyear}.id = summed_fields.funder_financial_year_id
    """,
    "Update funder makes_grants_to_individuals": """
    WITH individual_funders AS (
        SELECT DISTINCT ffy.funder_id
        FROM
            {ukgrantmaking_funderfinancialyear} ffy,
            {ukgrantmaking_financialyear} fy
        WHERE
            ffy.financial_year_id = fy.fy
            AND (fy."current" = TRUE OR fy.status IN ('Open', 'Future'))
            AND spending_grant_making_individuals > 0
    )
    UPDATE {ukgrantmaking_funder}
    SET makes_grants_to_individuals = TRUE
    FROM individual_funders
    WHERE {ukgrantmaking_funder}.org_id = individual_funders.funder_id
    """,
    "Update current funder financial years with the latest funder data": """
    UPDATE
        {ukgrantmaking_funderfinancialyear}
    SET
        segment = f.segment,
        included = f.included,
        makes_grants_to_individuals = f.makes_grants_to_individuals
    FROM
        {ukgrantmaking_financialyear} fy,
        {ukgrantmaking_funder} f
    WHERE
        {ukgrantmaking_funderfinancialyear}.financial_year_id = fy.fy
        AND {ukgrantmaking_funderfinancialyear}.funder_id = f.org_id
        AND (fy."current" = TRUE OR fy.status IN ('Open', 'Future'))
    """,
    "Ensure that the current funder financial year has the correct tags": """
    INSERT INTO
        {ukgrantmaking_funderfinancialyear_tags} (funderfinancialyear_id, fundertag_id)
    SELECT
        ffy.id AS funderfinancialyear_id,
        ft.fundertag_id AS fundertag_id
    FROM
        {ukgrantmaking_funderfinancialyear} ffy
        INNER JOIN {ukgrantmaking_financialyear} fy ON ffy.financial_year_id = fy.fy
        INNER JOIN {ukgrantmaking_funder_tags} ft ON ffy.funder_id = ft.funder_id
    WHERE
        (fy."current" = TRUE OR fy.status IN ('Open', 'Future'))
    ON CONFLICT (funderfinancialyear_id, fundertag_id) DO NOTHING
    """,
    "Remove existing tags from the current funder financial year": """
    DELETE 
    FROM {ukgrantmaking_funderfinancialyear_tags}
    WHERE id IN (
        SELECT t.id 
        FROM {ukgrantmaking_funderfinancialyear_tags} t
            INNER JOIN {ukgrantmaking_funderfinancialyear} ffy ON ffy.id = t.funderfinancialyear_id
            INNER JOIN {ukgrantmaking_financialyear} fy ON ffy.financial_year_id = fy.fy
            LEFT OUTER JOIN {ukgrantmaking_funder_tags} ft ON ffy.funder_id = ft.funder_id
                AND ft.fundertag_id = t.fundertag_id 
        WHERE ft.fundertag_id IS NULL
            AND (fy."current" = TRUE OR fy.status IN ('Open', 'Future'))
    )
    """,
}


def format_query(query):
    FinancialYear = apps.get_model("ukgrantmaking", "FinancialYear")
    FunderFinancialYear = apps.get_model("ukgrantmaking", "FunderFinancialYear")
    FunderYear = apps.get_model("ukgrantmaking", "FunderYear")
    Funder = apps.get_model("ukgrantmaking", "Funder")

    return query.format(
        ukgrantmaking_funder=Funder._meta.db_table,
        ukgrantmaking_funderfinancialyear=FunderFinancialYear._meta.db_table,
        ukgrantmaking_financialyear=FinancialYear._meta.db_table,
        ukgrantmaking_funderyear=FunderYear._meta.db_table,
        ukgrantmaking_funderfinancialyear_tags=FunderFinancialYear.tags.through._meta.db_table,
        ukgrantmaking_funder_tags=Funder.tags.through._meta.db_table,
    )


@click.command()
def financial_year():
    with transaction.atomic(), connection.cursor() as cursor:
        for query_name, query in SQL_QUERIES.items():
            logger.info(f"[Query] Started:  {query_name}")
            cursor.execute(format_query(query))
            logger.info(f"[Query] Completed: {query_name}")
            logger.info(f"[Query] Rows affected: {cursor.rowcount:,.0f}")
