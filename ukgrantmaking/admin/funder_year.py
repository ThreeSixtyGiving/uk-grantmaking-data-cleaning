from django.contrib import admin
from django.utils.html import format_html

from ukgrantmaking.admin.csv_upload import CSVUploadModelAdmin
from ukgrantmaking.models.funder_year import FunderYear


class FunderYearInline(admin.StackedInline):
    model = FunderYear
    fk_name = "funder_financial_year"
    extra = 0
    readonly_fields = (
        "income",
        "income_investment",
        "spending",
        "spending_investment",
        "spending_charitable",
        "spending_grant_making",
        "spending_grant_making_individuals",
        "spending_grant_making_institutions_charitable",
        "spending_grant_making_institutions_noncharitable",
        "spending_grant_making_institutions_unknown",
        "spending_grant_making_institutions",
        "accounts_link",
        "total_net_assets_registered",
        "funds_registered",
        "funds_endowment_registered",
        "funds_restricted_registered",
        "funds_unrestricted_registered",
        "employees_registered",
    )
    show_change_link = True
    can_delete = False
    max_num = None
    ordering = ("-financial_year_end",)
    fieldsets = (
        (
            "Edit details",
            {
                "classes": (
                    "collapse",
                    "extrapretty",
                ),
                "fields": [
                    (
                        "financial_year_end",
                        "financial_year_start",
                        "funder_financial_year",
                        "accounts_link",
                    ),
                    (
                        "income",
                        "income_investment",
                        "spending",
                        "spending_investment",
                        "spending_charitable",
                        "spending_grant_making",
                    ),
                    (
                        "spending_grant_making_individuals",
                        "spending_grant_making_individuals_manual",
                    ),
                    (
                        "spending_grant_making_institutions_charitable",
                        "spending_grant_making_institutions_charitable_manual",
                    ),
                    (
                        "spending_grant_making_institutions_noncharitable",
                        "spending_grant_making_institutions_noncharitable_manual",
                    ),
                    (
                        "spending_grant_making_institutions_unknown",
                        "spending_grant_making_institutions_unknown_manual",
                    ),
                    ("spending_grant_making_institutions",),
                ],
            },
        ),
        (
            "Assets and Employees",
            {
                "classes": (
                    "collapse",
                    "extrapretty",
                ),
                "fields": [
                    ("total_net_assets_registered", "total_net_assets_manual"),
                    ("funds_registered", "funds_manual"),
                    ("funds_endowment_registered", "funds_endowment_manual"),
                    ("funds_restricted_registered", "funds_restricted_manual"),
                    ("funds_unrestricted_registered", "funds_unrestricted_manual"),
                    ("employees_registered", "employees_manual"),
                ],
            },
        ),
    )

    @admin.display(description="")
    def accounts_link(self, obj):
        link = None
        if obj.funder_id.startswith("GB-CHC-"):
            link = "https://ccew.dkane.net/charity/{}/accounts/{}".format(
                obj.funder_id.replace("GB-CHC-", ""),
                obj.financial_year_end,
            )
        if link:
            return format_html(
                '<a href="{}" target="_blank">Open Accounts PDF</a>', link
            )
        return ""


class FunderYearAdmin(CSVUploadModelAdmin):
    list_display = (
        "funder__org_id",
        "funder__name",
        "fy",
        "financial_year_end",
        "funder__segment",
        "funder__category",
        "funder__included",
        "income",
        "spending",
        "spending_charitable",
    )
    show_facets = admin.ShowFacets.ALWAYS
    list_display_links = ("financial_year_end",)
    search_fields = ("funder_financial_year__funder__name",)
    list_filter = (
        "funder_financial_year__included",
        "funder_financial_year__financial_year__fy",
        "funder_financial_year__segment",
        "funder_financial_year__category",
    )
    readonly_fields = (
        "income_registered",
        "income",
        "income_investment_registered",
        "spending_registered",
        "spending_investment_registered",
        "spending_charitable_registered",
        "spending_grant_making",
        "spending_grant_making_individuals_registered",
        "spending_grant_making_individuals_360Giving",
        "spending_grant_making_institutions_charitable_registered",
        "spending_grant_making_institutions_charitable_360Giving",
        "spending_grant_making_institutions_noncharitable_registered",
        "spending_grant_making_institutions_noncharitable_360Giving",
        "spending_grant_making_institutions_unknown_registered",
        "spending_grant_making_institutions_unknown_360Giving",
        "spending_grant_making_institutions",
        "total_net_assets_registered",
        "funds_registered",
        "funds_endowment_registered",
        "funds_restricted_registered",
        "funds_unrestricted_registered",
        "employees_registered",
        "date_added",
        "date_updated",
        # "funder_financial_year",
        # "new_funder_financial_year",
    )
    autocomplete_fields = ("funder_financial_year", "new_funder_financial_year")
    # raw_id_fields = ("funder",)
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "funder_financial_year",
                    (
                        "financial_year_end",
                        "financial_year_start",
                        # "financial_year",
                    ),
                    "new_funder_financial_year",
                ]
            },
        ),
        (
            "Income",
            {
                "fields": [
                    ("income_registered", "income_manual"),
                    ("income_investment_registered", "income_investment_manual"),
                ]
            },
        ),
        (
            "Spending",
            {
                "fields": [
                    ("spending_registered", "spending_manual"),
                    ("spending_investment_registered", "spending_investment_manual"),
                    ("spending_charitable_registered", "spending_charitable_manual"),
                    ("spending_grant_making",),
                    (
                        "spending_grant_making_individuals_registered",
                        "spending_grant_making_individuals_360Giving",
                        "spending_grant_making_individuals_manual",
                    ),
                    (
                        "spending_grant_making_institutions_charitable_registered",
                        "spending_grant_making_institutions_charitable_360Giving",
                        "spending_grant_making_institutions_charitable_manual",
                    ),
                    (
                        "spending_grant_making_institutions_noncharitable_registered",
                        "spending_grant_making_institutions_noncharitable_360Giving",
                        "spending_grant_making_institutions_noncharitable_manual",
                    ),
                    (
                        "spending_grant_making_institutions_unknown_registered",
                        "spending_grant_making_institutions_unknown_360Giving",
                        "spending_grant_making_institutions_unknown_manual",
                    ),
                    ("spending_grant_making_institutions",),
                ]
            },
        ),
        (
            "Assets",
            {
                "fields": [
                    ("total_net_assets_registered", "total_net_assets_manual"),
                    ("funds_registered", "funds_manual"),
                    ("funds_endowment_registered", "funds_endowment_manual"),
                    ("funds_restricted_registered", "funds_restricted_manual"),
                    ("funds_unrestricted_registered", "funds_unrestricted_manual"),
                ]
            },
        ),
        (
            "Employees",
            {
                "fields": [
                    (
                        "employees_registered",
                        "employees_manual",
                    )
                ]
            },
        ),
        (
            "Checked",
            {
                "fields": [
                    "date_added",
                    "date_updated",
                ]
            },
        ),
    )

    @admin.display(description="Financial Year")
    def fy(self, obj):
        return obj.funder_financial_year.financial_year.fy

    @admin.display(description="Segment")
    def funder__segment(self, obj):
        return obj.funder_financial_year.segment

    @admin.display(description="Category")
    def funder__category(self, obj):
        return obj.funder_financial_year.category

    @admin.display(description="Included", boolean=True)
    def funder__included(self, obj):
        return obj.funder_financial_year.included

    @admin.display(description="Funder ID")
    def funder__org_id(self, obj):
        return obj.funder_financial_year.funder.org_id

    @admin.display(description="Funder Name")
    def funder__name(self, obj):
        return obj.funder_financial_year.funder.name
