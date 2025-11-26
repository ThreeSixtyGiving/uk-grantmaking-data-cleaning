from django.db import models
from django_db_views.db_view import DBView


class GrantsAnalysisView(DBView):
    # --- Primary Key / Grant Details ---
    grant_id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=512, verbose_name="Grant Title")
    description = models.TextField(verbose_name="Grant Description", null=True)
    currency = models.CharField(max_length=10, verbose_name="Currency")
    amount_awarded = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Amount Awarded"
    )

    amount_awarded_gbp = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        db_column="amount_awarded_GBP",
        verbose_name="Amount Awarded (GBP)",
    )
    award_date = models.DateField(verbose_name="Award Date", null=True)
    regrant_type = models.CharField(
        max_length=50, verbose_name="Regrant Type", null=True
    )

    # --- Duration Details ---
    planned_dates_duration = models.IntegerField(
        verbose_name="Planned Duration (Months)", null=True
    )
    planned_dates_start_date = models.DateField(
        db_column="planned_dates_startDate",
        verbose_name="Planned Start Date",
        null=True,
    )
    planned_dates_end_date = models.DateField(
        db_column="planned_dates_endDate", verbose_name="Planned End Date", null=True
    )
    inclusion = models.CharField(
        max_length=50, verbose_name="Inclusion Status", null=True
    )

    # --- Derived Bands ---
    duration_band = models.CharField(max_length=50, verbose_name="Duration Band")
    grant_amount_band = models.CharField(
        max_length=50, verbose_name="Grant Amount Band"
    )

    # --- Recipient Details ---
    recipient_id = models.CharField(max_length=50, verbose_name="Recipient ID")
    recipient_organisation_id = models.CharField(
        max_length=50, verbose_name="Recipient Org ID", null=True
    )
    recipient_organisation_name = models.CharField(
        max_length=255, verbose_name="Recipient Org Name"
    )
    recipient_type = models.CharField(
        max_length=50, verbose_name="Recipient Type", null=True
    )
    regulator_name = models.CharField(
        max_length=255, verbose_name="Regulator Name", db_column="regulator_name"
    )
    regulator_type = models.CharField(
        max_length=50, verbose_name="Regulator Type", db_column="regulator_type"
    )
    regulator_date_of_registration = models.DateField(
        verbose_name="Regulator Registration Date",
        db_column="regulator_date_of_registration",
        null=True,
    )
    regulator_scale = models.CharField(
        max_length=50,
        verbose_name="Regulator Scale",
        db_column="regulator_scale",
        null=True,
    )
    regulator_how = models.CharField(
        max_length=255,
        verbose_name="Regulator How",
        db_column="regulator_how",
        null=True,
    )
    regulator_who = models.CharField(
        max_length=255,
        verbose_name="Regulator Who",
        db_column="regulator_who",
        null=True,
    )
    regulator_what = models.CharField(
        max_length=255,
        verbose_name="Regulator What",
        db_column="regulator_what",
        null=True,
    )

    # Regulator London/Location Details
    regulator_london_aoo = models.BooleanField(
        verbose_name="Regulator AOO is London",
        db_column="regulator_london_aoo",
        null=True,
    )
    regulator_london_hq = models.BooleanField(
        verbose_name="Regulator HQ is London",
        db_column="regulator_london_hq",
        null=True,
    )

    regulator_ctry_hq_name = models.CharField(
        max_length=255,
        verbose_name="Regulator HQ Country Name",
        db_column="regulator_ctry_hq_name",
        null=True,
    )
    regulator_rgn_hq_name = models.CharField(
        max_length=255,
        verbose_name="Regulator HQ Region Name",
        db_column="regulator_rgn_hq_name",
        null=True,
    )
    regulator_la_hq_name = models.CharField(
        max_length=255,
        verbose_name="Regulator HQ LA Name",
        db_column="regulator_la_hq_name",
        null=True,
    )
    regulator_ctry_aoo_name = models.CharField(
        max_length=255,
        verbose_name="Regulator AOO Country Name",
        db_column="regulator_ctry_aoo_name",
        null=True,
    )
    regulator_rgn_aoo_name = models.CharField(
        max_length=255,
        verbose_name="Regulator AOO Region Name",
        db_column="regulator_rgn_aoo_name",
        null=True,
    )
    regulator_la_aoo_name = models.CharField(
        max_length=255,
        verbose_name="Regulator AOO LA Name",
        db_column="regulator_la_aoo_name",
        null=True,
    )

    # --- Recipient Year Regulator Data ---
    financial_year_end = models.DateField(
        verbose_name="Recipient Financial Year End", null=True
    )
    income = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Recipient Income", null=True
    )
    spending = models.DecimalField(
        max_digits=18, decimal_places=2, verbose_name="Recipient Spending", null=True
    )
    employees = models.IntegerField(verbose_name="Recipient Employees", null=True)
    income_band = models.CharField(
        max_length=50, verbose_name="Income Band (Org Size)", null=True
    )

    # --- Funder Details ---
    funding_organisation_id = models.CharField(
        max_length=50, verbose_name="Funding Org ID"
    )
    funding_organisation_name = models.CharField(
        max_length=255, verbose_name="Funding Org Name"
    )
    funding_organisation_department = models.CharField(
        max_length=255, verbose_name="Funding Org Department", null=True
    )
    funder_id = models.CharField(max_length=50, verbose_name="Funder ID")
    funding_organisation_type = models.CharField(
        max_length=50, verbose_name="Funding Org Type"
    )
    funder_segment = models.CharField(
        max_length=50, db_column="segment", verbose_name="Funder Segment"
    )
    funder_category = models.CharField(
        max_length=50, db_column="category", verbose_name="Funder Category"
    )
    funder_name = models.CharField(
        max_length=255, db_column="funder_name", verbose_name="Funder Name"
    )

    # Funder Location Details
    funder_la_hq_name = models.CharField(
        max_length=255, verbose_name="Funder HQ LA Name", null=True
    )
    funder_rgn_hq_name = models.CharField(
        max_length=255, verbose_name="Funder HQ Region Name", null=True
    )
    funder_ctry_hq_name = models.CharField(
        max_length=255, verbose_name="Funder HQ Country Name", null=True
    )
    funder_la_aoo_name = models.CharField(
        max_length=255, verbose_name="Funder AOO LA Name", null=True
    )
    funder_rgn_aoo_name = models.CharField(
        max_length=255, verbose_name="Funder AOO Region Name", null=True
    )
    funder_ctry_aoo_name = models.CharField(
        max_length=255, verbose_name="Funder AOO Country Name", null=True
    )

    # --- View SQL Definition ---
    view_definition = {
        "django.db.backends.postgresql": """
        SELECT
            -- grant details
            g.grant_id, 
            g.title, 
            g.description, 
            g.currency, 
            g.amount_awarded, 
            g."amount_awarded_GBP" AS amount_awarded_gbp, 
            g.award_date, 
            g.regrant_type,

            -- duration details
            g.planned_dates_duration, 
            g."planned_dates_startDate" AS planned_dates_start_date, 
            g."planned_dates_endDate" AS planned_dates_end_date, 
            g.inclusion,

            -- *** Duration Band ***
            CASE
                WHEN g.planned_dates_duration IS NULL OR g.planned_dates_duration = 0 THEN 'Unknown/0'
                WHEN g.planned_dates_duration > 0 AND g.planned_dates_duration <= 6 THEN 'Up to 6 months'
                WHEN g.planned_dates_duration > 6 AND g.planned_dates_duration <= 12 THEN '7-12 months'
                WHEN g.planned_dates_duration > 12 AND g.planned_dates_duration <= 35 THEN '13-35 months'
                WHEN g.planned_dates_duration >= 36 THEN '3+ years'
                ELSE 'Other'
            END AS duration_band,

            -- *** Grant Amount Band ***
            CASE
                WHEN g."amount_awarded_GBP" IS NULL OR g."amount_awarded_GBP" = 0 THEN 'Zero/unknown'
                WHEN g."amount_awarded_GBP" > 0 AND g."amount_awarded_GBP" < 1000 THEN 'Under £1k'
                WHEN g."amount_awarded_GBP" >= 1000 AND g."amount_awarded_GBP" < 10000 THEN '£1k - £10k'
                WHEN g."amount_awarded_GBP" >= 10000 AND g."amount_awarded_GBP" < 100000 THEN '£10k - £100k'
                WHEN g."amount_awarded_GBP" >= 100000 AND g."amount_awarded_GBP" <= 1000000 THEN '£100k - £1m'
                WHEN g."amount_awarded_GBP" > 1000000 THEN 'Over £1m'
                ELSE 'Other'
            END AS grant_amount_band,

            -- recipient details (from grant table)
            g.recipient_id, 
            g.recipient_organisation_id, 
            g.recipient_organisation_name, 
            g.recipient_type, -- g.recipient_type (original grant field)

            -- recipient regulator details (from recipient table 'r')
            r.name AS regulator_name, 
            r.type AS regulator_type, 
            r.date_of_registration AS regulator_date_of_registration, 
            r.scale AS regulator_scale, 
            r.how AS regulator_how, 
            r.who AS regulator_who, 
            r.what AS regulator_what, 
            r.london_aoo AS regulator_london_aoo, 
            r.london_hq AS regulator_london_hq, 
            r.ctry_hq_name AS regulator_ctry_hq_name, 
            r.rgn_hq_name AS regulator_rgn_hq_name,
            r.la_hq_name AS regulator_la_hq_name,
            r.ctry_aoo_name AS regulator_ctry_aoo_name, 
            r.rgn_aoo_name AS regulator_rgn_aoo_name,
            r.la_aoo_name AS regulator_la_aoo_name,

            -- recipient year regulator data - financials
            y.financial_year_end, 
            y.income, 
            y.spending, 
            y.employees,

            -- *** Income Band (organisation size) ***
            CASE
                WHEN y.income IS NULL THEN 'Unknown'
                WHEN y.income < 10000 THEN 'Under £10k'
                WHEN y.income >= 10000 AND y.income <= 100000 THEN '£10k to £100k'
                WHEN y.income > 100000 AND y.income <= 1000000 THEN '£100k to £1m'
                WHEN y.income > 1000000 AND y.income <= 10000000 THEN '£1m to £10m'
                WHEN y.income > 10000000 THEN 'Over £10m'
                ELSE 'Other'
            END AS income_band,

            -- funder details
            g.funding_organisation_id, 
            g.funding_organisation_name, 
            g.funding_organisation_department,
            g.funder_id, 
            g.funding_organisation_type, 
            f.segment AS funder_segment, 
            f.category AS funder_category, 
            f.name AS funder_name,
            f.la_hq_name AS funder_la_hq_name,
            f.rgn_hq_name AS funder_rgn_hq_name,
            f.ctry_hq_name AS funder_ctry_hq_name,
            f.la_aoo_name AS funder_la_aoo_name,
            f.rgn_aoo_name AS funder_rgn_aoo_name,
            f.ctry_aoo_name AS funder_ctry_aoo_name


        FROM ukgrantmaking_grant g
        LEFT JOIN ukgrantmaking_grantrecipient r
        ON g.recipient_id = r.recipient_id
        LEFT JOIN ukgrantmaking_grantrecipientyear y
        ON g.recipient_id = y.recipient_id
        AND g.financial_year_id = y.financial_year_id
        LEFT JOIN ukgrantmaking_funder f
        ON g.funder_id = f.org_id
        JOIN ukgrantmaking_financialyear ukgfy
        ON g.financial_year_id = ukgfy.fy
        WHERE ukgfy.current = TRUE
        """
    }

    class Meta:
        managed = False
        db_table = "ukgrantmaking_grants_analysis_view"
