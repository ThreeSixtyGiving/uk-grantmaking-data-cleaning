# Generated by Django 5.0.6 on 2024-11-15 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ukgrantmaking", "0070_alter_fundernote_added_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cleaningstatus",
            name="sort_by",
            field=models.CharField(
                choices=[
                    (
                        "Grantmaker",
                        [
                            ("financial_year_end", "Financial Year End"),
                            ("income", "Income"),
                            ("income_investment", "Income investment"),
                            ("spending", "Spending"),
                            ("spending_investment", "Spending investment"),
                            ("spending_charitable", "Spending charitable"),
                            ("spending_grant_making", "Spending grant making"),
                            (
                                "spending_grant_making_individuals",
                                "Spending grant making individuals",
                            ),
                            (
                                "spending_grant_making_institutions_charitable",
                                "Spending grant making institutions charitable",
                            ),
                            (
                                "spending_grant_making_institutions_noncharitable",
                                "Spending grant making institutions noncharitable",
                            ),
                            (
                                "spending_grant_making_institutions_unknown",
                                "Spending grant making institutions unknown",
                            ),
                            (
                                "spending_grant_making_institutions",
                                "Spending grant making institutions",
                            ),
                            ("total_net_assets", "Total net assets"),
                            ("funds", "Funds"),
                            ("funds_endowment", "Funds endowment"),
                            ("funds_restricted", "Funds restricted"),
                            ("funds_unrestricted", "Funds unrestricted"),
                            ("employees", "Employees"),
                            ("checked", "Checked"),
                            ("financial_year__funder__org_id", "Funder ID"),
                            ("financial_year__funder__name", "Funder Name"),
                            ("financial_year__tags", "Tags"),
                            ("financial_year__segment", "Segment"),
                            ("financial_year__included", "Included"),
                            (
                                "financial_year__makes_grants_to_individuals",
                                "Makes grants to individuals",
                            ),
                            ("financial_year__segment_checked", "Segment checked"),
                            ("financial_year__checked", "Checked"),
                            ("financial_year__checked_on", "Checked on"),
                            ("financial_year__checked_by", "Checked by"),
                            ("financial_year__notes", "Notes"),
                            ("financial_year__date_added", "Date added"),
                            ("financial_year__date_updated", "Date updated"),
                        ],
                    ),
                    (
                        "Grant",
                        [
                            ("title", "Title"),
                            ("description", "Description"),
                            ("currency", "Currency"),
                            ("amount_awarded", "Amount awarded"),
                            ("amount_awarded_GBP", "Amount awarded GBP"),
                            ("award_date", "Award date"),
                            ("planned_dates_duration", "Planned dates duration"),
                            ("planned_dates_startDate", "Planned dates startDate"),
                            ("planned_dates_endDate", "Planned dates endDate"),
                            ("recipient_organisation_id", "Recipient organisation id"),
                            (
                                "recipient_organisation_name",
                                "Recipient organisation name",
                            ),
                            ("recipient_individual_id", "Recipient individual id"),
                            ("recipient_individual_name", "Recipient individual name"),
                            (
                                "recipient_individual_primary_grant_reason",
                                "Recipient individual primary grant reason",
                            ),
                            (
                                "recipient_individual_secondary_grant_reason",
                                "Recipient individual secondary grant reason",
                            ),
                            (
                                "recipient_individual_grant_purpose",
                                "Recipient individual grant purpose",
                            ),
                            ("recipient_type", "Recipient type"),
                            ("funding_organisation_id", "Funding organisation id"),
                            ("funding_organisation_name", "Funding organisation name"),
                            ("funding_organisation_type", "Funding organisation type"),
                            ("regrant_type", "Regrant type"),
                            ("location_scope", "Location scope"),
                            ("grant_programme_title", "Grant programme title"),
                            ("publisher_prefix", "Publisher prefix"),
                            ("publisher_name", "Publisher name"),
                            ("license", "License"),
                            ("recipient_location_rgn", "Recipient location rgn"),
                            ("recipient_location_ctry", "Recipient location ctry"),
                            ("beneficiary_location_rgn", "Beneficiary location rgn"),
                            ("beneficiary_location_ctry", "Beneficiary location ctry"),
                            ("funder", "Funder"),
                            ("recipient", "Recipient"),
                            ("recipient_type_manual", "Recipient type manual"),
                            ("inclusion", "Inclusion"),
                            ("notes", "Notes"),
                            ("checked_by", "Checked by"),
                            ("annual_amount", "Annual amount"),
                        ],
                    ),
                ],
                default="spending_grant_making",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="cleaningstatusquery",
            name="field",
            field=models.CharField(
                choices=[
                    (
                        "Grantmaker",
                        [
                            ("financial_year_end", "Financial Year End"),
                            ("income", "Income"),
                            ("income_investment", "Income investment"),
                            ("spending", "Spending"),
                            ("spending_investment", "Spending investment"),
                            ("spending_charitable", "Spending charitable"),
                            ("spending_grant_making", "Spending grant making"),
                            (
                                "spending_grant_making_individuals",
                                "Spending grant making individuals",
                            ),
                            (
                                "spending_grant_making_institutions_charitable",
                                "Spending grant making institutions charitable",
                            ),
                            (
                                "spending_grant_making_institutions_noncharitable",
                                "Spending grant making institutions noncharitable",
                            ),
                            (
                                "spending_grant_making_institutions_unknown",
                                "Spending grant making institutions unknown",
                            ),
                            (
                                "spending_grant_making_institutions",
                                "Spending grant making institutions",
                            ),
                            ("total_net_assets", "Total net assets"),
                            ("funds", "Funds"),
                            ("funds_endowment", "Funds endowment"),
                            ("funds_restricted", "Funds restricted"),
                            ("funds_unrestricted", "Funds unrestricted"),
                            ("employees", "Employees"),
                            ("checked", "Checked"),
                            ("financial_year__funder__org_id", "Funder ID"),
                            ("financial_year__funder__name", "Funder Name"),
                            ("financial_year__tags", "Tags"),
                            ("financial_year__segment", "Segment"),
                            ("financial_year__included", "Included"),
                            (
                                "financial_year__makes_grants_to_individuals",
                                "Makes grants to individuals",
                            ),
                            ("financial_year__segment_checked", "Segment checked"),
                            ("financial_year__checked", "Checked"),
                            ("financial_year__checked_on", "Checked on"),
                            ("financial_year__checked_by", "Checked by"),
                            ("financial_year__notes", "Notes"),
                            ("financial_year__date_added", "Date added"),
                            ("financial_year__date_updated", "Date updated"),
                        ],
                    ),
                    (
                        "Grant",
                        [
                            ("title", "Title"),
                            ("description", "Description"),
                            ("currency", "Currency"),
                            ("amount_awarded", "Amount awarded"),
                            ("amount_awarded_GBP", "Amount awarded GBP"),
                            ("award_date", "Award date"),
                            ("planned_dates_duration", "Planned dates duration"),
                            ("planned_dates_startDate", "Planned dates startDate"),
                            ("planned_dates_endDate", "Planned dates endDate"),
                            ("recipient_organisation_id", "Recipient organisation id"),
                            (
                                "recipient_organisation_name",
                                "Recipient organisation name",
                            ),
                            ("recipient_individual_id", "Recipient individual id"),
                            ("recipient_individual_name", "Recipient individual name"),
                            (
                                "recipient_individual_primary_grant_reason",
                                "Recipient individual primary grant reason",
                            ),
                            (
                                "recipient_individual_secondary_grant_reason",
                                "Recipient individual secondary grant reason",
                            ),
                            (
                                "recipient_individual_grant_purpose",
                                "Recipient individual grant purpose",
                            ),
                            ("recipient_type", "Recipient type"),
                            ("funding_organisation_id", "Funding organisation id"),
                            ("funding_organisation_name", "Funding organisation name"),
                            ("funding_organisation_type", "Funding organisation type"),
                            ("regrant_type", "Regrant type"),
                            ("location_scope", "Location scope"),
                            ("grant_programme_title", "Grant programme title"),
                            ("publisher_prefix", "Publisher prefix"),
                            ("publisher_name", "Publisher name"),
                            ("license", "License"),
                            ("recipient_location_rgn", "Recipient location rgn"),
                            ("recipient_location_ctry", "Recipient location ctry"),
                            ("beneficiary_location_rgn", "Beneficiary location rgn"),
                            ("beneficiary_location_ctry", "Beneficiary location ctry"),
                            ("funder", "Funder"),
                            ("recipient", "Recipient"),
                            ("recipient_type_manual", "Recipient type manual"),
                            ("inclusion", "Inclusion"),
                            ("notes", "Notes"),
                            ("checked_by", "Checked by"),
                            ("annual_amount", "Annual amount"),
                        ],
                    ),
                ],
                max_length=50,
            ),
        ),
    ]