from django.contrib import admin
from django.utils.html import format_html

from ukgrantmaking.admin.csv_upload import CSVUploadModelAdmin
from ukgrantmaking.models import (
    FunderNote,
    FunderYear,
)


class FunderYearInline(admin.StackedInline):
    model = FunderYear
    extra = 0
    readonly_fields = (
        "income",
        "spending",
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
                    "funder_financial_year__funder",
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
                    (
                        "checked_by",
                        "notes",
                    ),
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


class FunderNoteInline(admin.TabularInline):
    model = FunderNote
    extra = 0
    fields = (
        "note",
        "date_added",
        "added_by",
    )
    readonly_fields = ("date_added",)
    show_change_link = False
    can_delete = False

    def has_change_permission(self, request, obj):
        return False


class FunderAdmin(CSVUploadModelAdmin):
    list_display = (
        "org_id",
        "name",
        "segment",
        "included",
        "makes_grants_to_individuals",
        "size",
        "tag_list",
        "checked_by",
        "checked",
    )
    search_fields = ("name", "org_id")
    list_filter = (
        "included",
        "segment",
        ("segment", admin.EmptyFieldListFilter),
        "tags",
        "makes_grants_to_individuals",
        "org_id_schema",
        # "latest_year__checked",
        ("latest_year", admin.EmptyFieldListFilter),
    )
    show_facets = admin.ShowFacets.NEVER
    list_editable = (
        "included",
        "segment",
        "makes_grants_to_individuals",
    )
    filter_horizontal = ("tags",)
    inlines = (
        # FunderYearInline,
        FunderNoteInline,
    )
    readonly_fields = (
        "name_registered",
        "date_of_registration",
        "activities",
        "ftc_link",
    )
    autocomplete_fields = ("successor",)
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "org_id",
                    ("charity_number", "ftc_link"),
                    ("name_registered", "name_manual"),
                    "successor",
                    "segment",
                    "tags",
                    "included",
                    "makes_grants_to_individuals",
                    "date_of_registration",
                    "activities",
                ]
            },
        ),
    )

    @admin.display(description="Latest grantmaking")
    def size(self, obj):
        if obj.latest_year:
            return "{:,.0f}".format(obj.latest_year.spending_grant_making)

    @admin.display(description="Tags")
    def tag_list(self, obj):
        return "; ".join([tag.tag for tag in obj.tags.all()])

    @admin.display(description="Checked by")
    def checked_by(self, obj):
        return obj.latest_year.checked_by if obj.latest_year else None

    @admin.display(description="Checked", boolean=True)
    def checked(self, obj):
        return obj.latest_year.checked if obj.latest_year else None

    @admin.display(description="")
    def ftc_link(self, obj):
        return format_html(
            '<a href="https://findthatcharity.uk/orgid/{}" target="_blank">Find that Charity</a>',
            obj.org_id,
        )


class FunderTagAdmin(admin.ModelAdmin):
    list_display = ("tag", "funder_count", "description", "parent")
    list_editable = ("parent",)
    ordering = ("parent", "tag")

    def funder_count(self, obj):
        return obj.funders.count()


class FunderYearAdmin(CSVUploadModelAdmin):
    list_display = (
        "funder__org_id",
        "funder__name",
        "fy",
        "financial_year_end",
        "funder__segment",
        "funder__included",
        "income",
        "spending",
        "spending_charitable",
        "checked",
    )
    show_facets = admin.ShowFacets.ALWAYS
    list_display_links = ("financial_year_end",)
    search_fields = ("funder_financial_year__funder__name",)
    list_filter = (
        "funder_financial_year__included",
        "funder_financial_year__financial_year__fy",
        "funder_financial_year__segment",
        "checked",
        ("checked_by", admin.EmptyFieldListFilter),
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
        "checked_on",
        "checked",
        "date_added",
        "date_updated",
        # "financial_year",
    )
    # raw_id_fields = ("funder",)
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "funder",
                    (
                        "financial_year_end",
                        "financial_year_start",
                        # "financial_year",
                    ),
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
                    "checked",
                    "checked_on",
                    "checked_by",
                    "notes",
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

    @admin.display(description="Included", boolean=True)
    def funder__included(self, obj):
        return obj.funder_financial_year.included

    @admin.display(description="Funder ID")
    def funder__org_id(self, obj):
        return obj.funder_financial_year.funder.org_id

    @admin.display(description="Funder Name")
    def funder__name(self, obj):
        return obj.funder_financial_year.funder.name
