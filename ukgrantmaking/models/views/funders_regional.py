from django.db import models
from django_db_views.db_view import DBView


class FundersRegionalView(DBView):
    org_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Name")
    segment = models.CharField(max_length=50, verbose_name="Segment")
    category = models.CharField(max_length=50, verbose_name="Category")
    scale = models.CharField(max_length=255, null=True, verbose_name="Funder Scale")
    include_in_analysis = models.BooleanField(
        null=True, verbose_name="Include in Analysis"
    )
    grantmaking = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        verbose_name="Grantmaking GBP m",
    )
    geoarea = models.CharField(
        max_length=255, null=True, verbose_name="Geographical Area"
    )
    overseas = models.BooleanField(null=True, verbose_name="Overseas")

    england = models.BooleanField(null=True, verbose_name="England")
    northern_ireland = models.BooleanField(null=True, verbose_name="Northern Ireland")
    scotland = models.BooleanField(null=True, verbose_name="Scotland")
    wales = models.BooleanField(null=True, verbose_name="Wales")

    england_northeast = models.BooleanField(
        null=True, verbose_name="England - North East"
    )
    england_northwest = models.BooleanField(
        null=True, verbose_name="England - North West"
    )
    england_yorkshire = models.BooleanField(
        null=True, verbose_name="England - Yorkshire and the Humber"
    )
    england_eastmidlands = models.BooleanField(
        null=True, verbose_name="England - East Midlands"
    )
    england_westmidlands = models.BooleanField(
        null=True, verbose_name="England - West Midlands"
    )
    england_east = models.BooleanField(
        null=True, verbose_name="England - East of England"
    )
    england_london = models.BooleanField(null=True, verbose_name="England - London")
    england_southeast = models.BooleanField(
        null=True, verbose_name="England - South East"
    )
    england_southwest = models.BooleanField(
        null=True, verbose_name="England - South West"
    )

    # --- View SQL Definition ---
    view_definition = {
        "django.db.backends.postgresql": """
        WITH base AS (
            SELECT org_id,
                "name",
                segment,
                category,
                "scale",
                "include_in_analysis",
                f."year1_Grantmaking_GBP_m" AS "grantmaking",
                "scale" ILIKE '%%overseas%%' AS "overseas",
                ctry_aoo::jsonb ? 'E92000001' AS "england",
                ctry_aoo::jsonb ? 'N92000002' AS "northern_ireland",
                ctry_aoo::jsonb ? 'S92000003' AS "scotland",
                ctry_aoo::jsonb ? 'W92000004' AS "wales",
                rgn_aoo::jsonb ? 'E12000001' AS "england_northeast",
                rgn_aoo::jsonb ? 'E12000002' AS "england_northwest",
                rgn_aoo::jsonb ? 'E12000003' AS "england_yorkshire",
                rgn_aoo::jsonb ? 'E12000004' AS "england_eastmidlands",
                rgn_aoo::jsonb ? 'E12000005' AS "england_westmidlands",
                rgn_aoo::jsonb ? 'E12000006' AS "england_east",
                rgn_aoo::jsonb ? 'E12000007' AS "england_london",
                rgn_aoo::jsonb ? 'E12000008' AS "england_southeast",
                rgn_aoo::jsonb ? 'E12000009' AS "england_southwest"
            FROM ukgrantmaking_funders_analysis_view f
            ORDER BY f."year1_Grantmaking_Rank"
        )
        SELECT org_id,
            "name",
            segment,
            category,
            "scale",
            "include_in_analysis",
            grantmaking,
            CASE WHEN "scale" IN ('National and Overseas', 'Overseas') THEN "scale"
                WHEN "scale" = 'National' THEN 
                    CASE WHEN "england" AND "northern_ireland" AND "scotland" AND "wales" THEN 'United Kingdom'
                        WHEN "england" AND "scotland" AND "wales" THEN 'Great Britain'
                        WHEN "england" AND "wales" THEN 'England and Wales'
                        WHEN "england" THEN 'England'
                        WHEN "wales" THEN 'Wales'
                        WHEN "scotland" THEN 'Scotland'
                        WHEN "northern_ireland" THEN 'Northern Ireland'
                        ELSE 'Other National' END
                WHEN "scale" = 'Regional' THEN 'Regional'
                WHEN "scale" = 'Local' THEN 'Local'
                ELSE 'Other' END AS "geoarea",
            "overseas",
            "england",
            "northern_ireland",
            "scotland",
            "wales",
            "england_northeast",
            "england_northwest",
            "england_yorkshire",
            "england_eastmidlands",
            "england_westmidlands",
            "england_east",
            "england_london",
            "england_southeast",
            "england_southwest"
        FROM base
        ORDER BY grantmaking DESC NULLS LAST
        """
    }

    class Meta:
        managed = False
        db_table = "ukgrantmaking_funders_regional_view"
