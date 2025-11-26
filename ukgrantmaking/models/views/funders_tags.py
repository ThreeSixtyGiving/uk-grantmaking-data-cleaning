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
            SUM(CASE WHEN tag = '360Giving Publisher' THEN 1 ELSE 0 END) > 0 AS funders_360_giving_publisher,
            SUM(CASE WHEN tag = 'Living Wage Funder' THEN 1 ELSE 0 END) > 0 AS living_wage_funder,
            SUM(CASE WHEN tag = 'ACO' THEN 1 ELSE 0 END) > 0 AS aco,
            SUM(CASE WHEN tag = 'ACF Current' THEN 1 ELSE 0 END) > 0 AS acf_current,
            SUM(CASE WHEN tag = 'London Funders' THEN 1 ELSE 0 END) > 0 AS london_funders,
            SUM(CASE WHEN tag = 'Yorkshire Funders' THEN 1 ELSE 0 END) > 0 AS yorkshire_funders,
            SUM(CASE WHEN tag = 'West Midlands Funders Network' THEN 1 ELSE 0 END) > 0 AS west_midlands_funders_network,
            SUM(CASE WHEN tag = 'VONNE' THEN 1 ELSE 0 END) > 0 AS vonne,
            SUM(CASE WHEN tag = 'Open & Trusting' THEN 1 ELSE 0 END) > 0 AS open_trusting,
            SUM(CASE WHEN tag = 'Postcode Lottery' THEN 1 ELSE 0 END) > 0 AS postcode_lottery,
            SUM(CASE WHEN tag = 'Sainsburys Family Charitable Trusts' THEN 1 ELSE 0 END) > 0 AS sainsburys_family_charitable_trusts,
            SUM(CASE WHEN tag = 'Funders Forum for NI' THEN 1 ELSE 0 END) > 0 AS funders_forum_for_ni,
            SUM(CASE WHEN tag = 'UKCF' THEN 1 ELSE 0 END) > 0 AS ukcf,
            SUM(CASE WHEN tag = 'Community Foundation' THEN 1 ELSE 0 END) > 0 AS community_foundation,
            SUM(CASE WHEN tag = 'Livery Company' THEN 1 ELSE 0 END) > 0 AS livery_company,
            SUM(CASE WHEN tag = 'CCEW' THEN 1 ELSE 0 END) > 0 AS ccew,
            SUM(CASE WHEN tag = 'OSCR' THEN 1 ELSE 0 END) > 0 AS oscr,
            SUM(CASE WHEN tag = 'CCNI' THEN 1 ELSE 0 END) > 0 AS ccni
        FROM
            (
                SELECT DISTINCT
                    ukgfv.org_id,
                    ukgfv.name,
                    unnest(string_to_array(ukgfv.tags_list,';')) AS "tag"
                FROM
                    ukgrantmaking_funders_view ukgfv
                JOIN
                    ukgrantmaking_financialyear ukgfy ON ukgfv.fy = ukgfy.fy
                WHERE
                    ukgfy.current = TRUE
            ) AS unnested_tags
        GROUP BY
            org_id, name
        """
    }

    class Meta:
        managed = False
        db_table = "ukgrantmaking_funders_tags_view"
