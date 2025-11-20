from django.contrib.postgres.fields import ArrayField
from django.db import models
from django_db_views.db_view import DBView

from ukgrantmaking.models.funder_utils import FunderCategory, FunderSegment


class FundersView(DBView):
    org_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    segment = models.CharField(
        max_length=50,
        choices=FunderSegment.choices,
        default=FunderSegment.GENERAL_FOUNDATION,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Funder segment",
    )
    category = models.CharField(
        max_length=50,
        choices=FunderCategory.choices,
        default=FunderCategory.TRUSTS_FOUNDATIONS,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Funder category",
    )
    makes_grants_to_individuals = models.BooleanField(null=True)
    tags = ArrayField(models.CharField(max_length=100), null=True)
    fy = models.CharField(max_length=9)
    financial_year_end = models.DateField(null=True)
    income = models.BigIntegerField(null=True)
    income_investment = models.BigIntegerField(null=True)
    spending = models.BigIntegerField(null=True)
    spending_investment = models.BigIntegerField(null=True)
    spending_charitable = models.BigIntegerField(null=True)
    spending_grant_making = models.BigIntegerField(null=True)
    spending_grant_making_individuals = models.BigIntegerField(null=True)
    spending_grant_making_institutions = models.BigIntegerField(null=True)
    total_net_assets = models.BigIntegerField(null=True)
    funds = models.BigIntegerField(null=True)
    funds_endowment = models.BigIntegerField(null=True)
    funds_restricted = models.BigIntegerField(null=True)
    funds_unrestricted = models.BigIntegerField(null=True)
    employees = models.IntegerField(null=True)
    employees_permanent = models.IntegerField(null=True)
    employees_fixedterm = models.IntegerField(null=True)
    employees_selfemployed = models.IntegerField(null=True)
    checked = models.TextField(null=True)
    checked_by_id = models.IntegerField(null=True)
    checked_on = models.DateTimeField(null=True)
    tags_list = models.TextField(null=True)
    tags_json = models.TextField(null=True)
    tags_json_text = models.TextField(null=True)
    segment_year = models.CharField(
        max_length=50,
        choices=FunderSegment.choices,
        default=FunderSegment.GENERAL_FOUNDATION,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Funder segment (in year)",
    )
    category_year = models.CharField(
        max_length=50,
        choices=FunderCategory.choices,
        default=FunderCategory.TRUSTS_FOUNDATIONS,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Funder category (in year)",
    )
    makes_grants_to_individuals_year = models.BooleanField(null=True)
    tags_list_year = models.TextField(null=True)
    included_year = models.BooleanField(null=True)

    @property
    def id(self):
        return f"{self.org_id}-{self.fy}"

    def _get_pk_val(self, meta=None):
        return f"{self.org_id}-{self.fy}"

    pk = property(_get_pk_val, DBView._set_pk_val)

    view_definition = {
        "django.db.backends.postgresql": """
            WITH fy AS (
                SELECT *
                FROM ukgrantmaking_financialyear
                WHERE status IN ('Open', 'Closed')
                    OR "current" 
                ORDER BY fy DESC
                LIMIT 5
            ),
            spend_data AS (
                SELECT coalesce(new_funder_financial_year_id, funder_financial_year_id) AS funder_financial_year_id,
                    max(financial_year_end) AS financial_year_end,
                    sum(income) AS income,
                    sum(income_investment) AS income_investment,
                    sum(spending) AS spending,
                    sum(spending_investment) AS spending_investment,
                    sum(spending_charitable) AS spending_charitable,
                    sum(spending_grant_making) AS spending_grant_making,
                    sum(spending_grant_making_individuals) AS spending_grant_making_individuals,
                    sum(spending_grant_making_institutions) AS spending_grant_making_institutions
                FROM ukgrantmaking_funderyear
                GROUP BY 1
            ),
            balance_sheet AS (
                SELECT DISTINCT ON (coalesce(new_funder_financial_year_id, funder_financial_year_id))
                    coalesce(new_funder_financial_year_id, funder_financial_year_id) AS funder_financial_year_id,
                    financial_year_end,
                    total_net_assets,
                    funds,
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
                        funds_endowment IS NOT NULL OR  
                        funds_restricted IS NOT NULL OR  
                        funds_unrestricted IS NOT NULL
                    ) then coalesce(funds_endowment, 0) else null end as funds_endowment,
                    case when (
                        funds_endowment IS NOT NULL OR  
                        funds_restricted IS NOT NULL OR  
                        funds_unrestricted IS NOT NULL
                    ) then coalesce(funds_restricted, 0) else null end as funds_restricted,
                    case when (
                        funds_endowment IS NOT NULL OR  
                        funds_restricted IS NOT NULL OR  
                        funds_unrestricted IS NOT NULL
                    ) then coalesce(funds_unrestricted, 0) else null end as funds_unrestricted,
                    employees,
                    case when (
                        employees_permanent IS NOT NULL OR  
                        employees_fixedterm IS NOT NULL OR  
                        employees_selfemployed IS NOT NULL
                    ) then (
                        coalesce(employees_permanent, 0) + 
                        coalesce(employees_fixedterm, 0) + 
                        coalesce(employees_selfemployed, 0)
                    ) else null end as employees_calculated,
                    case when (
                        employees_permanent IS NOT NULL OR  
                        employees_fixedterm IS NOT NULL OR  
                        employees_selfemployed IS NOT NULL
                    ) then coalesce(employees_permanent, 0) else null end as employees_permanent,
                    case when (
                        employees_permanent IS NOT NULL OR  
                        employees_fixedterm IS NOT NULL OR  
                        employees_selfemployed IS NOT NULL
                    ) then coalesce(employees_fixedterm, 0) else null end as employees_fixedterm,
                    case when (
                        employees_permanent IS NOT NULL OR  
                        employees_fixedterm IS NOT NULL OR  
                        employees_selfemployed IS NOT NULL
                    ) then coalesce(employees_selfemployed, 0) else null end as employees_selfemployed
                FROM ukgrantmaking_funderyear
                ORDER BY coalesce(new_funder_financial_year_id, funder_financial_year_id),
                    financial_year_end DESC
            ),
            tags_year AS (
                SELECT funderfinancialyear_id,
                    array_agg(t.tag) AS tags,
                    string_agg(t.tag, ';') AS tags_list,
                    json_agg(t.tag) AS tags_json
                FROM ukgrantmaking_funderfinancialyear_tags ffyt
                    INNER JOIN ukgrantmaking_fundertag t
                        ON ffyt.fundertag_id = t.slug 
                GROUP BY 1
            ),
            tags AS (
                SELECT funder_id,
                    array_agg(t.tag) AS tags,
                    string_agg(t.tag, ';') AS tags_list,
                    json_agg(t.tag) AS tags_json
                FROM ukgrantmaking_funder_tags ft
                    INNER JOIN ukgrantmaking_fundertag t
                        ON ft.fundertag_id = t.slug 
                GROUP BY 1
            )
            SELECT f.org_id,
                f."name",
                f.segment,
                f.category,
                f.makes_grants_to_individuals,
                tags.tags,
                fy.fy,
                spend_data.financial_year_end,
                spend_data.income,
                spend_data.income_investment,
                spend_data.spending,
                spend_data.spending_investment,
                spend_data.spending_charitable,
                spend_data.spending_grant_making,
                spend_data.spending_grant_making_individuals,
                spend_data.spending_grant_making_institutions,
                coalesce(
                    balance_sheet.total_net_assets,
                    balance_sheet.funds_calculated
                ) AS total_net_assets,
                coalesce(
                    balance_sheet.funds,
                    balance_sheet.funds_calculated
                ) AS funds,
                balance_sheet.funds_endowment,
                balance_sheet.funds_restricted,
                balance_sheet.funds_unrestricted,
                balance_sheet.employees,
                balance_sheet.employees_permanent,
                balance_sheet.employees_fixedterm,
                balance_sheet.employees_selfemployed,
                ffy.checked,
                ffy.checked_by_id,
                ffy.checked_on,
                tags.tags_list,
                tags.tags_json,
                tags.tags_json::TEXT AS tags_json_text,
                ffy.segment AS segment_year,
                ffy.category AS category_year,
                ffy.makes_grants_to_individuals AS makes_grants_to_individuals_year,
                tags_year.tags_list as tags_list_year,
                ffy.included AS included_year
            FROM ukgrantmaking_funderfinancialyear ffy 
                INNER JOIN fy
                    ON ffy.financial_year_id = fy.fy 
                INNER JOIN ukgrantmaking_funder f
                    ON ffy.funder_id = f.org_id 
                LEFT OUTER JOIN tags_year
                    ON tags_year.funderfinancialyear_id = ffy.id
                LEFT OUTER JOIN tags
                    ON tags.funder_id = f.org_id
                LEFT OUTER JOIN spend_data
                    ON spend_data.funder_financial_year_id = ffy.id
                LEFT OUTER JOIN balance_sheet
                    ON balance_sheet.funder_financial_year_id = ffy.id
            WHERE f.included
            ORDER BY fy.fy DESC, spending_grant_making DESC NULLS LAST
        """
    }

    class Meta:
        managed = False  # Managed must be set to False!
        db_table = "ukgrantmaking_funders_view"
