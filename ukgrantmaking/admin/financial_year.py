from django.contrib import admin

# from ukgrantmaking.models.financial_years import FinancialYear


class FinancialYearAdmin(admin.ModelAdmin):
    list_display = (
        "fy",
        "funders_start_date",
        "funders_end_date",
        "grants_start_date",
        "grants_end_date",
        "current",
        "status",
    )
    list_editable = (
        "current",
        "status",
    )
