from django.contrib import admin

from ukgrantmaking.admin.csv_upload import CSVUploadModelAdmin
from ukgrantmaking.admin.funder_year import FunderYearInline
from ukgrantmaking.models.funder_financial_year import FunderFinancialYear


class FunderFinancialYearInline(admin.StackedInline):
    model = FunderFinancialYear
    fields = ("financial_year",)
    readonly_fields = ("financial_year",)
    show_change_link = True
    can_delete = False
    max_num = None
    extra = 0
    ordering = ("-financial_year_id",)


class FunderFinancialYearAdmin(CSVUploadModelAdmin):
    list_display = (
        "funder__org_id",
        "funder__name",
        "fy",
        "segment",
        "included",
        "income",
        "spending",
        "spending_charitable",
        "scaling",
        "checked",
    )
    readonly_fields = (
        "tags",
        "segment",
        "included",
        "makes_grants_to_individuals",
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
        "scaling",
        "total_net_assets",
        "funds",
        "funds_endowment",
        "funds_restricted",
        "funds_unrestricted",
        "employees",
        "employees_permanent",
        "employees_fixedterm",
        "employees_selfemployed",
    )
    search_fields = ("funder__name",)
    filter_horizontal = ("tags",)

    @admin.display(description="Financial Year")
    def fy(self, obj):
        return obj.financial_year.fy

    @admin.display(description="Funder ID")
    def funder__org_id(self, obj):
        return obj.funder.org_id

    @admin.display(description="Funder Name")
    def funder__name(self, obj):
        return obj.funder.name

    inlines = (FunderYearInline,)
