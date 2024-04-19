from django.contrib import admin

from ukgrantmaking.models import Funder, FunderNote, FunderTag, FunderYear

admin.site.site_title = "UK Grantmaking"
admin.site.site_header = "UK Grantmaking Data Cleaning"


class FunderYearInline(admin.TabularInline):
    model = FunderYear
    extra = 0
    fields = (
        "financial_year_end",
        "income",
        "spending",
        "spending_charitable",
        "spending_grant_making",
        "spending_grant_making_individuals",
        "spending_grant_making_institutions",
        "checked_by",
    )
    readonly_fields = (
        "financial_year_end",
        "income",
        "spending",
        "spending_charitable",
        "spending_grant_making",
        "spending_grant_making_individuals",
        "spending_grant_making_institutions",
        "checked_by",
    )
    show_change_link = True
    can_delete = False


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


@admin.register(Funder)
class FunderAdmin(admin.ModelAdmin):
    list_display = (
        "org_id",
        "name",
        "segment",
        "included",
        "makes_grants_to_individuals",
        "size",
        "tag_list",
        "checked_by",
    )
    search_fields = ("name", "org_id")
    list_filter = (
        "included",
        "segment",
        "tags",
        "makes_grants_to_individuals",
        "org_id_schema",
        ("latest_year", admin.EmptyFieldListFilter),
    )
    show_facets = admin.ShowFacets.NEVER
    list_editable = (
        "included",
        "segment",
        "makes_grants_to_individuals",
    )
    filter_horizontal = ("tags",)
    inlines = (FunderYearInline, FunderNoteInline)
    readonly_fields = (
        "name_registered",
        "date_of_registration",
        "activities",
        "latest_grantmaking",
    )
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "org_id",
                    "charity_number",
                    ("name_registered", "name_manual"),
                    "segment",
                    "tags",
                    "included",
                    "makes_grants_to_individuals",
                    "date_of_registration",
                    "activities",
                    "latest_grantmaking",
                ]
            },
        ),
    )

    @admin.display(description="Latest grantmaking")
    def size(self, obj):
        if obj.latest_grantmaking:
            return "{:,.0f}".format(obj.latest_grantmaking)

    @admin.display(description="Tags")
    def tag_list(self, obj):
        return "; ".join([tag.tag for tag in obj.tags.all()])

    @admin.display(description="Checked by")
    def checked_by(self, obj):
        return obj.latest_year.checked_by if obj.latest_year else None


@admin.register(FunderTag)
class FunderTagAdmin(admin.ModelAdmin):
    pass


@admin.register(FunderYear)
class FunderYearAdmin(admin.ModelAdmin):
    list_display = (
        "funder",
        "financial_year_end",
        "income",
        "spending",
        "spending_charitable",
    )
    show_facets = admin.ShowFacets.ALWAYS
    list_display_links = ("financial_year_end",)
    search_fields = ("funder__name",)
    list_filter = ("financial_year",)
    readonly_fields = (
        "income_registered",
        "income",
        "spending_registered",
        "spending_charitable_registered",
        "spending_grant_making",
        "spending_grant_making_individuals_registered",
        "spending_grant_making_institutions_registered",
        "total_net_assets_registered",
        "funds_registered",
        "funds_endowment_registered",
        "funds_restricted_registered",
        "funds_unrestricted_registered",
        "employees_registered",
        "checked_on",
        "date_added",
        "date_updated",
    )
    raw_id_fields = ("funder",)
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "funder",
                    ("financial_year_end", "financial_year_start"),
                ]
            },
        ),
        (
            "Income",
            {
                "fields": [
                    ("income_registered", "income_manual"),
                ]
            },
        ),
        (
            "Spending",
            {
                "fields": [
                    ("spending_registered", "spending_manual"),
                    ("spending_charitable_registered", "spending_charitable_manual"),
                    ("spending_grant_making",),
                    (
                        "spending_grant_making_individuals_registered",
                        "spending_grant_making_individuals_manual",
                    ),
                    (
                        "spending_grant_making_institutions_registered",
                        "spending_grant_making_institutions_manual",
                    ),
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
                    "checked_on",
                    "checked_by",
                    "notes",
                    "date_added",
                    "date_updated",
                ]
            },
        ),
    )
