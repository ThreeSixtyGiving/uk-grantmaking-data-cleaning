from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html

from ukgrantmaking.admin.csv_upload import CSVUploadModelAdmin
from ukgrantmaking.admin.funder_financial_year import FunderFinancialYearInline
from ukgrantmaking.models.funder import FunderNote
from ukgrantmaking.models.funder_utils import RecordStatus


class FunderTagAdmin(admin.ModelAdmin):
    list_display = ("tag", "funder_count", "description", "parent")
    list_editable = ("parent",)
    ordering = ("parent", "tag")

    def funder_count(self, obj):
        return obj.funders.count()


class FunderNoteInline(GenericTabularInline):
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
        "category",
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
        "category",
        ("segment", admin.EmptyFieldListFilter),
        "tags",
        "makes_grants_to_individuals",
        "org_id_schema",
        # "current_year__checked",
        ("current_year", admin.EmptyFieldListFilter),
    )
    show_facets = admin.ShowFacets.NEVER
    list_editable = (
        "included",
        "segment",
        "makes_grants_to_individuals",
    )
    filter_horizontal = ("tags",)
    inlines = (
        FunderFinancialYearInline,
        FunderNoteInline,
    )
    readonly_fields = (
        "name_registered",
        "date_of_registration",
        "activities",
        "ftc_link",
        "latest_scaling",
        "current_scaling",
        "latest_year",
        "current_year",
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
                    ("latest_year", "latest_scaling"),
                    ("current_year", "current_scaling"),
                ]
            },
        ),
    )

    @admin.display(description="Latest grantmaking")
    def size(self, obj):
        if obj.current_year and obj.current_year.spending_grant_making:
            return "{:,.0f}".format(obj.current_year.spending_grant_making)

    @admin.display(description="Tags")
    def tag_list(self, obj):
        return "; ".join([tag.tag for tag in obj.tags.all()])

    @admin.display(description="Checked by")
    def checked_by(self, obj):
        return obj.current_year.checked_by if obj.current_year else None

    @admin.display(description="Checked", boolean=True)
    def checked(self, obj):
        return (
            obj.current_year.checked == RecordStatus.CHECKED
            if obj.current_year
            else None
        )

    @admin.display(description="Grantmaker size (latest)")
    def latest_scaling(self, obj):
        if obj.latest_year:
            return obj.latest_year.scaling
        return None

    @admin.display(description="Grantmaker size (current)")
    def current_scaling(self, obj):
        if obj.current_year:
            return obj.current_year.scaling
        return None

    @admin.display(description="")
    def ftc_link(self, obj):
        return format_html(
            '<a href="https://findthatcharity.uk/orgid/{}" target="_blank">Find that Charity</a>',
            obj.org_id,
        )
