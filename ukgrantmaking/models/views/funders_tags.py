from django.db import models
from django_db_views.db_view import DBView


class FundersTagsView(DBView):
    org_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    funders_360_giving_publisher = models.BooleanField(
        null=True, verbose_name="360 Giving Publisher"
    )
    living_wage_funder = models.BooleanField(
        null=True, verbose_name="Living Wage Funder"
    )
    aco = models.BooleanField(null=True, verbose_name="ACO")
    acf_current = models.BooleanField(null=True, verbose_name="ACF Current")
    london_funders = models.BooleanField(null=True, verbose_name="London Funders")
    yorkshire_funders = models.BooleanField(null=True, verbose_name="Yorkshire Funders")
    west_midlands_funders_network = models.BooleanField(
        null=True, verbose_name="West Midlands Funders Network"
    )
    vonne = models.BooleanField(null=True, verbose_name="VONNE")
    open_trusting = models.BooleanField(null=True, verbose_name="Open & Trusting")
    postcode_lottery = models.BooleanField(null=True, verbose_name="Postcode Lottery")
    sainsburys_family_charitable_trusts = models.BooleanField(
        null=True, verbose_name="Sainsburys Family Charitable Trusts"
    )
    funders_forum_for_ni = models.BooleanField(
        null=True, verbose_name="Funders Forum for NI"
    )
    ukcf = models.BooleanField(null=True, verbose_name="UKCF")
    community_foundation = models.BooleanField(
        null=True, verbose_name="Community Foundation"
    )
    livery_company = models.BooleanField(null=True, verbose_name="Livery Company")
    ccew = models.BooleanField(null=True, verbose_name="CCEW")
    oscr = models.BooleanField(null=True, verbose_name="OSCR")
    ccni = models.BooleanField(null=True, verbose_name="CCNI")

    view_definition = {
        "django.db.backends.postgresql": """
        SELECT
            org_id,
            name,
            -- OUTPUT: TRUE/NULL for Boolean fields with snake_case aliases
            MAX(CASE WHEN tag = '360Giving Publisher' THEN TRUE ELSE NULL END) AS funders_360_giving_publisher,
            MAX(CASE WHEN tag = 'Living Wage Funder' THEN TRUE ELSE NULL END) AS living_wage_funder,
            MAX(CASE WHEN tag = 'ACO' THEN TRUE ELSE NULL END) AS aco,
            MAX(CASE WHEN tag = 'ACF Current' THEN TRUE ELSE NULL END) AS acf_current,
            MAX(CASE WHEN tag = 'London Funders' THEN TRUE END) AS london_funders,
            MAX(CASE WHEN tag = 'Yorkshire Funders' THEN TRUE END) AS yorkshire_funders,
            MAX(CASE WHEN tag = 'West Midlands Funders Network' THEN TRUE END) AS west_midlands_funders_network,
            MAX(CASE WHEN tag = 'VONNE' THEN TRUE END) AS vonne,
            MAX(CASE WHEN tag = 'Open & Trusting' THEN TRUE END) AS open_trusting,
            MAX(CASE WHEN tag = 'Postcode Lottery' THEN TRUE END) AS postcode_lottery,
            MAX(CASE WHEN tag = 'Sainsburys Family Charitable Trusts' THEN TRUE END) AS sainsburys_family_charitable_trusts,
            MAX(CASE WHEN tag = 'Funders Forum for NI' THEN TRUE END) AS funders_forum_for_ni,
            MAX(CASE WHEN tag = 'UKCF' THEN TRUE END) AS ukcf,
            MAX(CASE WHEN tag = 'Community Foundation' THEN TRUE END) AS community_foundation,
            MAX(CASE WHEN tag = 'Livery Company' THEN TRUE END) AS livery_company,
            MAX(CASE WHEN tag = 'CCEW' THEN TRUE END) AS ccew,
            MAX(CASE WHEN tag = 'OSCR' THEN TRUE END) AS oscr,
            MAX(CASE WHEN tag = 'CCNI' THEN TRUE END) AS ccni
        FROM
            (
                SELECT DISTINCT
                    ukgfv.org_id,
                    unnest(string_to_array(ukgfv.tags_list,';')) AS "tag"
                FROM
                    ukgrantmaking_funders_view ukgfv
                JOIN
                    ukgrantmaking_financialyear ukgfy ON ukgfv.fy = ukgfy.fy
                WHERE
                    ukgfy.current = TRUE -- Filter to the fy marked current
            ) AS unnested_tags
        GROUP BY
            org_id
        """
    }

    class Meta:
        managed = False  # Managed must be set to False!
        db_table = "ukgrantmaking_funders_tags_view"
