from django.db import models
from django_db_views.db_view import DBView


class FundersAnalysisView(DBView):
    org_id = models.CharField(max_length=50, primary_key=True)
    segment = models.CharField(max_length=50, verbose_name="Segment")
    category = models.CharField(max_length=50, verbose_name="Category")
    name = models.CharField(max_length=255, verbose_name="Name")
    html_name = models.TextField(verbose_name="HTML Name", db_column="HTML_name")

    # --- Financial Year 1 ---
    year1_fy = models.CharField(
        max_length=10,
        null=True,
        db_column="year1_fy",
        verbose_name="Year 1 Financial Year",
    )
    year1_financial_year_end = models.DateField(
        null=True, db_column="year1_financial_year_end", verbose_name="Year 1 End Date"
    )
    year1_grantmaking_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year1_Grantmaking_GBP_m",
        verbose_name="Year 1 Grantmaking_GBP_m",
    )
    year1_grantmaking_rank = models.IntegerField(
        null=True,
        db_column="year1_Grantmaking_Rank",
        verbose_name="Year 1 Grantmaking Rank",
    )
    year1_grantmaking_band = models.CharField(
        max_length=50,
        null=True,
        db_column="year1_Grantmaking_Band",
        verbose_name="Year 1 Grantmaking Band",
    )
    year1_grantmaking_individuals_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year1_Grantmaking_Individuals_GBP_m",
        verbose_name="Year 1 Individuals Grantmaking_GBP_m",
    )
    year1_grantmaking_individuals_rank = models.IntegerField(
        null=True,
        db_column="year1_Grantmaking_Individuals_Rank",
        verbose_name="Year 1 Individuals Grantmaking Rank",
    )
    year1_income_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year1_Income_GBP_m",
        verbose_name="Year 1 Income_GBP_m",
    )
    year1_spending_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year1_Spending_GBP_m",
        verbose_name="Year 1 Spending_GBP_m",
    )
    year1_net_assets_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year1_Net_Assets_GBP_m",
        verbose_name="Year 1 Net Assets_GBP_m",
    )
    year1_employees = models.IntegerField(
        null=True, db_column="year1_Employees", verbose_name="Year 1 Employees"
    )

    # --- Financial Year 2 ---
    year2_fy = models.CharField(
        max_length=10,
        null=True,
        db_column="year2_fy",
        verbose_name="Year 2 Financial Year",
    )
    year2_financial_year_end = models.DateField(
        null=True, db_column="year2_financial_year_end", verbose_name="Year 2 End Date"
    )
    year2_grantmaking_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year2_Grantmaking_GBP_m",
        verbose_name="Year 2 Grantmaking_GBP_m",
    )
    year2_grantmaking_rank = models.IntegerField(
        null=True,
        db_column="year2_Grantmaking_Rank",
        verbose_name="Year 2 Grantmaking Rank",
    )
    year2_grantmaking_band = models.CharField(
        max_length=50,
        null=True,
        db_column="year2_Grantmaking_Band",
        verbose_name="Year 2 Grantmaking Band",
    )
    year2_grantmaking_individuals_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year2_Grantmaking_Individuals_GBP_m",
        verbose_name="Year 2 Individuals Grantmaking_GBP_m",
    )
    year2_grantmaking_individuals_rank = models.IntegerField(
        null=True,
        db_column="year2_Grantmaking_Individuals_Rank",
        verbose_name="Year 2 Individuals Grantmaking Rank",
    )
    year2_income_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year2_Income_GBP_m",
        verbose_name="Year 2 Income_GBP_m",
    )
    year2_spending_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year2_Spending_GBP_m",
        verbose_name="Year 2 Spending_GBP_m",
    )
    year2_net_assets_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year2_Net_Assets_GBP_m",
        verbose_name="Year 2 Net Assets_GBP_m",
    )
    year2_employees = models.IntegerField(
        null=True, db_column="year2_Employees", verbose_name="Year 2 Employees"
    )

    # --- Financial Year 3 ---
    year3_fy = models.CharField(
        max_length=10,
        null=True,
        db_column="year3_fy",
        verbose_name="Year 3 Financial Year",
    )
    year3_financial_year_end = models.DateField(
        null=True, db_column="year3_financial_year_end", verbose_name="Year 3 End Date"
    )
    year3_grantmaking_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year3_Grantmaking_GBP_m",
        verbose_name="Year 3 Grantmaking_GBP_m",
    )
    year3_grantmaking_rank = models.IntegerField(
        null=True,
        db_column="year3_Grantmaking_Rank",
        verbose_name="Year 3 Grantmaking Rank",
    )
    year3_grantmaking_band = models.CharField(
        max_length=50,
        null=True,
        db_column="year3_Grantmaking_Band",
        verbose_name="Year 3 Grantmaking Band",
    )
    year3_grantmaking_individuals_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year3_Grantmaking_Individuals_GBP_m",
        verbose_name="Year 3 Individuals Grantmaking_GBP_m",
    )
    year3_grantmaking_individuals_rank = models.IntegerField(
        null=True,
        db_column="year3_Grantmaking_Individuals_Rank",
        verbose_name="Year 3 Individuals Grantmaking Rank",
    )
    year3_income_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year3_Income_GBP_m",
        verbose_name="Year 3 Income_GBP_m",
    )
    year3_spending_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year3_Spending_GBP_m",
        verbose_name="Year 3 Spending_GBP_m",
    )
    year3_net_assets_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year3_Net_Assets_GBP_m",
        verbose_name="Year 3 Net Assets_GBP_m",
    )
    year3_employees = models.IntegerField(
        null=True, db_column="year3_Employees", verbose_name="Year 3 Employees"
    )

    # --- Financial Year 4 ---
    year4_fy = models.CharField(
        max_length=10,
        null=True,
        db_column="year4_fy",
        verbose_name="Year 4 Financial Year",
    )
    year4_financial_year_end = models.DateField(
        null=True, db_column="year4_financial_year_end", verbose_name="Year 4 End Date"
    )
    year4_grantmaking_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year4_Grantmaking_GBP_m",
        verbose_name="Year 4 Grantmaking_GBP_m",
    )
    year4_grantmaking_rank = models.IntegerField(
        null=True,
        db_column="year4_Grantmaking_Rank",
        verbose_name="Year 4 Grantmaking Rank",
    )
    year4_grantmaking_band = models.CharField(
        max_length=50,
        null=True,
        db_column="year4_Grantmaking_Band",
        verbose_name="Year 4 Grantmaking Band",
    )
    year4_grantmaking_individuals_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year4_Grantmaking_Individuals_GBP_m",
        verbose_name="Year 4 Individuals Grantmaking_GBP_m",
    )
    year4_grantmaking_individuals_rank = models.IntegerField(
        null=True,
        db_column="year4_Grantmaking_Individuals_Rank",
        verbose_name="Year 4 Individuals Grantmaking Rank",
    )
    year4_income_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year4_Income_GBP_m",
        verbose_name="Year 4 Income_GBP_m",
    )
    year4_spending_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year4_Spending_GBP_m",
        verbose_name="Year 4 Spending_GBP_m",
    )
    year4_net_assets_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year4_Net_Assets_GBP_m",
        verbose_name="Year 4 Net Assets_GBP_m",
    )
    year4_employees = models.IntegerField(
        null=True, db_column="year4_Employees", verbose_name="Year 4 Employees"
    )

    # --- Financial Year 5 ---
    year5_fy = models.CharField(
        max_length=10,
        null=True,
        db_column="year5_fy",
        verbose_name="Year 5 Financial Year",
    )
    year5_financial_year_end = models.DateField(
        null=True, db_column="year5_financial_year_end", verbose_name="Year 5 End Date"
    )
    year5_grantmaking_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year5_Grantmaking_GBP_m",
        verbose_name="Year 5 Grantmaking_GBP_m",
    )
    year5_grantmaking_rank = models.IntegerField(
        null=True,
        db_column="year5_Grantmaking_Rank",
        verbose_name="Year 5 Grantmaking Rank",
    )
    year5_grantmaking_band = models.CharField(
        max_length=50,
        null=True,
        db_column="year5_Grantmaking_Band",
        verbose_name="Year 5 Grantmaking Band",
    )
    year5_grantmaking_individuals_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year5_Grantmaking_Individuals_GBP_m",
        verbose_name="Year 5 Individuals Grantmaking_GBP_m",
    )
    year5_grantmaking_individuals_rank = models.IntegerField(
        null=True,
        db_column="year5_Grantmaking_Individuals_Rank",
        verbose_name="Year 5 Individuals Grantmaking Rank",
    )
    year5_income_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year5_Income_GBP_m",
        verbose_name="Year 5 Income_GBP_m",
    )
    year5_spending_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year5_Spending_GBP_m",
        verbose_name="Year 5 Spending_GBP_m",
    )
    year5_net_assets_m = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        db_column="year5_Net_Assets_GBP_m",
        verbose_name="Year 5 Net Assets_GBP_m",
    )
    year5_employees = models.IntegerField(
        null=True, db_column="year5_Employees", verbose_name="Year 5 Employees"
    )

    # --- Funder Location/Regulator Details ---
    charity_number = models.CharField(
        max_length=20, null=True, verbose_name="Charity Number"
    )
    active = models.CharField(max_length=10, null=True, verbose_name="Active Status")
    date_of_registration = models.DateField(
        null=True, verbose_name="Date of Registration"
    )
    how = models.CharField(
        max_length=255, null=True, verbose_name="How Grants Are Made"
    )
    what = models.CharField(max_length=255, null=True, verbose_name="What Grants Cover")
    who = models.CharField(max_length=255, null=True, verbose_name="Who Grants Target")
    scale = models.CharField(max_length=255, null=True, verbose_name="Funder Scale")

    # HQ Location Codes and Names
    la_hq = models.CharField(
        max_length=50, null=True, verbose_name="HQ Local Authority Code"
    )
    la_hq_name = models.CharField(
        max_length=255, null=True, verbose_name="HQ Local Authority Name"
    )
    rgn_hq = models.CharField(max_length=50, null=True, verbose_name="HQ Region Code")
    rgn_hq_name = models.CharField(
        max_length=255, null=True, verbose_name="HQ Region Name"
    )
    ctry_hq = models.CharField(max_length=50, null=True, verbose_name="HQ Country Code")
    ctry_hq_name = models.CharField(
        max_length=255, null=True, verbose_name="HQ Country Name"
    )

    # AOO Location Codes and Names
    la_aoo = models.CharField(
        max_length=50, null=True, verbose_name="AOO Local Authority Code"
    )
    la_aoo_name = models.CharField(
        max_length=255, null=True, verbose_name="AOO Local Authority Name"
    )
    rgn_aoo = models.CharField(max_length=50, null=True, verbose_name="AOO Region Code")
    rgn_aoo_name = models.CharField(
        max_length=255, null=True, verbose_name="AOO Region Name"
    )
    ctry_aoo = models.CharField(
        max_length=50, null=True, verbose_name="AOO Country Code"
    )
    ctry_aoo_name = models.CharField(
        max_length=255, null=True, verbose_name="AOO Country Name"
    )
    overseas_aoo = models.CharField(
        max_length=50, null=True, verbose_name="AOO Overseas Country Code"
    )
    overseas_aoo_name = models.CharField(
        max_length=255, null=True, verbose_name="AOO Overseas Country Name"
    )

    london_aoo = models.BooleanField(
        null=False, db_column="london_aoo", verbose_name="Area of Operation is London"
    )
    london_hq = models.BooleanField(
        null=False, db_column="london_hq", verbose_name="Headquarters in London"
    )

    # analysis flags
    has_2yrs_grantmaking = models.BooleanField(
        null=False,
        db_column="has_2yrs_Grantmaking",
        verbose_name="Has 2 Yrs Grantmaking Data",
    )
    has_2yrs_grantmaking_individuals = models.BooleanField(
        null=False,
        db_column="has_2yrs_Grantmaking_Individuals",
        verbose_name="Has 2 Yrs Individuals Grantmaking Data",
    )
    has_2yrs_income = models.BooleanField(
        null=False, db_column="has_2yrs_Income", verbose_name="Has 2 Yrs Income Data"
    )
    has_2yrs_spending = models.BooleanField(
        null=False,
        db_column="has_2yrs_Spending",
        verbose_name="Has 2 Yrs Spending Data",
    )
    has_2yrs_net_assets = models.BooleanField(
        null=False,
        db_column="has_2yrs_Net_Assets",
        verbose_name="Has 2 Yrs Net Assets Data",
    )
    has_2yrs_employees = models.BooleanField(
        null=False,
        db_column="has_2yrs_Employees",
        verbose_name="Has 2 Yrs Employee Data",
    )

    has_3yrs_grantmaking = models.BooleanField(
        null=False,
        db_column="has_3yrs_Grantmaking",
        verbose_name="Has 3 Yrs Grantmaking Data",
    )
    has_3yrs_grantmaking_individuals = models.BooleanField(
        null=False,
        db_column="has_3yrs_Grantmaking_Individuals",
        verbose_name="Has 3 Yrs Individuals Grantmaking Data",
    )
    has_3yrs_income = models.BooleanField(
        null=False, db_column="has_3yrs_Income", verbose_name="Has 3 Yrs Income Data"
    )
    has_3yrs_spending = models.BooleanField(
        null=False,
        db_column="has_3yrs_Spending",
        verbose_name="Has 3 Yrs Spending Data",
    )
    has_3yrs_net_assets = models.BooleanField(
        null=False,
        db_column="has_3yrs_Net_Assets",
        verbose_name="Has 3 Yrs Net Assets Data",
    )
    has_3yrs_employees = models.BooleanField(
        null=False,
        db_column="has_3yrs_Employees",
        verbose_name="Has 3 Yrs Employee Data",
    )

    include_in_analysis = models.BooleanField(
        null=False, db_column="include_in_analysis", verbose_name="Include In Analysis"
    )
    makes_grants_to_individuals = models.BooleanField(
        null=True, verbose_name="Makes Grants to Individuals"
    )

    # --- View SQL Definition ---
    view_definition = {
        "django.db.backends.postgresql": """
        WITH ufv AS (
        SELECT 
            segment,
            category,
            org_id,
            name,
            fy,
            tags_list_year,
            financial_year_end,
            spending_grant_making,
            spending_grant_making_individuals,
            income,
            spending,
            total_net_assets,
            employees,
            makes_grants_to_individuals,
            -- Convert key metrics to millions
            spending_grant_making / 1000000.0 AS grantmaking_m,
            spending_grant_making_individuals / 1000000.0 AS grantmaking_individuals_m,
            income / 1000000.0 AS income_m,
            spending / 1000000.0 AS spending_m,
            total_net_assets / 1000000.0 AS net_assets_m,
            -- Define grantmaking bands
            CASE 
                WHEN spending_grant_making IS NULL OR spending_grant_making = 0 
                THEN 'Zero/Unknown Spend'
                WHEN spending_grant_making > 0 AND spending_grant_making < 100000 
                THEN 'Under £100k'
                WHEN spending_grant_making >= 100000 AND spending_grant_making <= 1000000 
                THEN '£100k-£1m'
                WHEN spending_grant_making > 1000000 AND spending_grant_making <= 10000000 
                THEN '£1m-£10m'
                WHEN spending_grant_making > 10000000 AND spending_grant_making <= 100000000 
                THEN '£10m-£100m'
                WHEN spending_grant_making > 100000000 
                THEN 'Over £100m'
            END AS grantmaking_band
        FROM ukgrantmaking_funders_view
        ),
        -- add funder regulator details from funder table
        funder_details AS (
            SELECT
                org_id,
                charity_number,
                active,
                date_of_registration,
                how,
                what,
                who,
                scale,
                postcode,
                -- HQ
                la_hq,
                la_hq_name,
                rgn_hq,
                rgn_hq_name,
                ctry_hq,
                ctry_hq_name,
                -- AOO
                la_aoo,
                la_aoo_name,
                rgn_aoo,
                rgn_aoo_name,
                ctry_aoo,
                ctry_aoo_name,
                overseas_aoo,
                overseas_aoo_name,
                -- London Analysis
                london_aoo,
                london_hq
            FROM ukgrantmaking_funder
        ),
        financial_year_base AS (
            SELECT ukgrantmaking_financialyear.fy,
                ukgrantmaking_financialyear.funders_start_date,
                ukgrantmaking_financialyear.funders_end_date,
                ukgrantmaking_financialyear.grants_start_date,
                ukgrantmaking_financialyear.grants_end_date,
                ukgrantmaking_financialyear.current,
                ukgrantmaking_financialyear.status
            FROM ukgrantmaking_financialyear
            WHERE (ukgrantmaking_financialyear.status::text = ANY (ARRAY['Open'::character varying, 'Closed'::character varying]::text[])) OR ukgrantmaking_financialyear.current
            ORDER BY ukgrantmaking_financialyear.fy DESC
            LIMIT 5
        ),
        financial_years AS (
            SELECT array_agg(fy) AS fya
            FROM financial_year_base
        )
        SELECT
            ufv.segment,
            ufv.category,
            ufv.org_id,
            ufv.name,
            -- Create HTML name with 360Giving logo for publishers based on the 360Giving publisher tag
        MAX(CASE
                WHEN tags_list_year ILIKE '%%360Giving Publisher%%'
                THEN CONCAT(ufv.name, '<small><img decoding="async" src="https://cdn.threesixtygiving.org/components/preview/assets/images/360-logos/icon/360giving-icon.svg" style="width: 24px;"></small>')
                ELSE ufv.name
            END) AS "HTML_name",

            -- Add key metrics for last 5 years
            -- year 1(most recent) 
            MAX(fy) FILTER (WHERE fy = fya[1]) AS "year1_fy",
            MAX(financial_year_end) FILTER (WHERE fy = fya[1]) AS "year1_financial_year_end",
            MAX(grantmaking_m) FILTER (WHERE fy = fya[1]) AS "year1_Grantmaking_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making) FILTER (WHERE fy = fya[1]) DESC NULLS LAST) AS "year1_Grantmaking_Rank",
            MAX(grantmaking_band) FILTER (WHERE fy = fya[1]) AS "year1_Grantmaking_Band",
            MAX(grantmaking_individuals_m) FILTER (WHERE fy = fya[1]) AS "year1_Grantmaking_Individuals_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making_individuals) FILTER (WHERE fy = fya[1]) DESC NULLS LAST) AS "year1_Grantmaking_Individuals_Rank",
            MAX(income_m) FILTER (WHERE fy = fya[1]) AS "year1_Income_GBP_m",
            MAX(spending_m) FILTER (WHERE fy = fya[1]) AS "year1_Spending_GBP_m",
            MAX(net_assets_m) FILTER (WHERE fy = fya[1]) AS "year1_Net_Assets_GBP_m",
            MAX(employees) FILTER (WHERE fy = fya[1]) AS "year1_Employees",
            
            -- year 2 
            MAX(fy) FILTER (WHERE fy = fya[2]) AS "year2_fy",
            MAX(financial_year_end) FILTER (WHERE fy = fya[2]) AS "year2_financial_year_end",
            MAX(grantmaking_m) FILTER (WHERE fy = fya[2]) AS "year2_Grantmaking_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making) FILTER (WHERE fy = fya[2]) DESC NULLS LAST) AS "year2_Grantmaking_Rank",
            MAX(grantmaking_band) FILTER (WHERE fy = fya[2]) AS "year2_Grantmaking_Band",
            MAX(grantmaking_individuals_m) FILTER (WHERE fy = fya[2]) AS "year2_Grantmaking_Individuals_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making_individuals) FILTER (WHERE fy = fya[2]) DESC NULLS LAST) AS "year2_Grantmaking_Individuals_Rank",
            MAX(income_m) FILTER (WHERE fy = fya[2]) AS "year2_Income_GBP_m",
            MAX(spending_m) FILTER (WHERE fy = fya[2]) AS "year2_Spending_GBP_m",
            MAX(net_assets_m) FILTER (WHERE fy = fya[2]) AS "year2_Net_Assets_GBP_m",
            MAX(employees) FILTER (WHERE fy = fya[2]) AS "year2_Employees",
            
            -- year 3
            MAX(fy) FILTER (WHERE fy = fya[3]) AS "year3_fy",
            MAX(financial_year_end) FILTER (WHERE fy = fya[3]) AS "year3_financial_year_end",
            MAX(grantmaking_m) FILTER (WHERE fy = fya[3]) AS "year3_Grantmaking_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making) FILTER (WHERE fy = fya[3]) DESC NULLS LAST) AS "year3_Grantmaking_Rank",
            MAX(grantmaking_band) FILTER (WHERE fy = fya[3]) AS "year3_Grantmaking_Band",
            MAX(grantmaking_individuals_m) FILTER (WHERE fy = fya[3]) AS "year3_Grantmaking_Individuals_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making_individuals) FILTER (WHERE fy = fya[3]) DESC NULLS LAST) AS "year3_Grantmaking_Individuals_Rank",
            MAX(income_m) FILTER (WHERE fy = fya[3]) AS "year3_Income_GBP_m",
            MAX(spending_m) FILTER (WHERE fy = fya[3]) AS "year3_Spending_GBP_m",
            MAX(net_assets_m) FILTER (WHERE fy = fya[3]) AS "year3_Net_Assets_GBP_m",
            MAX(employees) FILTER (WHERE fy = fya[3]) AS "year3_Employees",
            
            -- year 4
            MAX(fy) FILTER (WHERE fy = fya[4]) AS "year4_fy",
            MAX(financial_year_end) FILTER (WHERE fy = fya[4]) AS "year4_financial_year_end",
            MAX(grantmaking_m) FILTER (WHERE fy = fya[4]) AS "year4_Grantmaking_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making) FILTER (WHERE fy = fya[4]) DESC NULLS LAST) AS "year4_Grantmaking_Rank",
            MAX(grantmaking_band) FILTER (WHERE fy = fya[4]) AS "year4_Grantmaking_Band",
            MAX(grantmaking_individuals_m) FILTER (WHERE fy = fya[4]) AS "year4_Grantmaking_Individuals_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making_individuals) FILTER (WHERE fy = fya[4]) DESC NULLS LAST) AS "year4_Grantmaking_Individuals_Rank",
            MAX(income_m) FILTER (WHERE fy = fya[4]) AS "year4_Income_GBP_m",
            MAX(spending_m) FILTER (WHERE fy = fya[4]) AS "year4_Spending_GBP_m",
            MAX(net_assets_m) FILTER (WHERE fy = fya[4]) AS "year4_Net_Assets_GBP_m",
            MAX(employees) FILTER (WHERE fy = fya[4]) AS "year4_Employees",
            
            -- year 5
            MAX(fy) FILTER (WHERE fy = fya[5]) AS "year5_fy",
            MAX(financial_year_end) FILTER (WHERE fy = fya[5]) AS "year5_financial_year_end",
            MAX(grantmaking_m) FILTER (WHERE fy = fya[5]) AS "year5_Grantmaking_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making) FILTER (WHERE fy = fya[5]) DESC NULLS LAST) AS "year5_Grantmaking_Rank",
            MAX(grantmaking_band) FILTER (WHERE fy = fya[5]) AS "year5_Grantmaking_Band",
            MAX(grantmaking_individuals_m) FILTER (WHERE fy = fya[5]) AS "year5_Grantmaking_Individuals_GBP_m",
            ROW_NUMBER() OVER (ORDER BY MAX(spending_grant_making_individuals) FILTER (WHERE fy = fya[5]) DESC NULLS LAST) AS "year5_Grantmaking_Individuals_Rank",
            MAX(income_m) FILTER (WHERE fy = fya[5]) AS "year5_Income_GBP_m",
            MAX(spending_m) FILTER (WHERE fy = fya[5]) AS "year5_Spending_GBP_m",
            MAX(net_assets_m) FILTER (WHERE fy = fya[5]) AS "year5_Net_Assets_GBP_m",
            MAX(employees) FILTER (WHERE fy = fya[5]) AS "year5_Employees",
            
            -- Funder location/regulator details 
            MAX(fd.charity_number) AS charity_number,
            MAX(fd.active::text) AS active, 
            MAX(fd.date_of_registration) AS date_of_registration,
            MAX(fd.how::text) AS how,  
            MAX(fd.what::text) AS what, 
            MAX(fd.who::text) AS who,
            MAX(fd.scale::text) AS scale,

            -- HQ Location Codes and Names
            MAX(fd.la_hq::text) AS la_hq,
            MAX(fd.la_hq_name::text) AS la_hq_name,
            MAX(fd.rgn_hq::text) AS rgn_hq,
            MAX(fd.rgn_hq_name::text) AS rgn_hq_name, 
            MAX(fd.ctry_hq::text) AS ctry_hq,
            MAX(fd.ctry_hq_name::text) AS ctry_hq_name,

            -- AOO Location Codes and Names
            MAX(fd.la_aoo::text) AS la_aoo,
            MAX(fd.la_aoo_name::text) AS la_aoo_name,
            MAX(fd.rgn_aoo::text) AS rgn_aoo,
            MAX(fd.rgn_aoo_name::text) AS rgn_aoo_name,  
            MAX(fd.ctry_aoo::text) AS ctry_aoo,
            MAX(fd.ctry_aoo_name::text) AS ctry_aoo_name,  
            MAX(fd.overseas_aoo::text) AS overseas_aoo,
            MAX(fd.overseas_aoo_name::text) AS overseas_aoo_name,  
            
            MAX(fd.london_aoo::text) AS london_aoo, 
            MAX(fd.london_hq::text) AS london_hq,  
            
            -- check for 2 years of data (last 2 years) 
            (COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2]) AND spending_grant_making IS NOT NULL) = 2) AS "has_2yrs_Grantmaking",
            (COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2]) AND spending_grant_making_individuals IS NOT NULL) = 2) AS "has_2yrs_Grantmaking_Individuals",
            (COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2]) AND income IS NOT NULL) = 2) AS "has_2yrs_Income",
            (COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2]) AND spending IS NOT NULL) = 2) AS "has_2yrs_Spending",
            (COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2]) AND total_net_assets IS NOT NULL) = 2) AS "has_2yrs_Net_Assets",
            (COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2]) AND employees IS NOT NULL) = 2) AS "has_2yrs_Employees",
            
            COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2], fya[3]) AND spending_grant_making IS NOT NULL) = 3 AS "has_3yrs_Grantmaking",
            COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2], fya[3]) AND spending_grant_making_individuals IS NOT NULL) = 3 AS "has_3yrs_Grantmaking_Individuals",
            COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2], fya[3]) AND income IS NOT NULL) = 3 AS "has_3yrs_Income",
            COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2], fya[3]) AND spending IS NOT NULL) = 3 AS "has_3yrs_Spending",
            COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2], fya[3]) AND total_net_assets IS NOT NULL) = 3 AS "has_3yrs_Net_Assets",
            COUNT(*) FILTER (WHERE fy IN (fya[1], fya[2], fya[3]) AND employees IS NOT NULL) = 3 AS "has_3yrs_Employees",

            (CASE
            WHEN MAX(income) FILTER (WHERE fy = fya[1]) IS NULL 
            AND MAX(spending_grant_making) FILTER (WHERE fy = fya[1]) IS NULL 
            THEN 0

            WHEN MAX(income) FILTER (WHERE fy = fya[1]) < 5000 
            AND MAX(spending_grant_making) FILTER (WHERE fy = fya[1]) < 5000 
            THEN 0

            ELSE 1
            END) > 0 AS "include_in_analysis",
            ufv.makes_grants_to_individuals
        FROM
            ufv
        LEFT JOIN funder_details fd ON ufv.org_id = fd.org_id,
            financial_years
        GROUP BY
            ufv.segment,
            ufv.category,
            ufv.org_id,
            ufv.name,
            ufv.makes_grants_to_individuals
        ORDER BY 
            MAX(spending_grant_making) FILTER (WHERE fy = fya[1]) DESC NULLS LAST
        """
    }

    class Meta:
        managed = False
        db_table = "ukgrantmaking_funders_analysis_view"
