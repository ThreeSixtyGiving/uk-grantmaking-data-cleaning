import os

from django.contrib import admin, messages
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import connection, transaction
from django.utils.html import format_html

from ukgrantmaking.admin.csv_upload import CSVUploadModelAdmin
from ukgrantmaking.admin.funder_financial_year import FunderFinancialYearInline
from ukgrantmaking.admin.utils import Action, add_admin_actions
from ukgrantmaking.management.commands.funders.fetch_ftc import (
    do_ftc_finance,
    do_ftc_funders,
)
from ukgrantmaking.management.commands.funders.update_financial_year import (
    SQL_QUERIES,
    format_query,
)
from ukgrantmaking.models.funder import FunderNote
from ukgrantmaking.models.funder_utils import (
    FunderSegment,
    RecordStatus,
)


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
    actions = [
        "refresh_from_findthatcharity",
        "set_as_included",
        "set_as_excluded",
        "set_as_makes_grants_to_individuals",
        "set_as_not_makes_grants_to_individuals",
    ]

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

    @admin.action(description="Refresh from Find that Charity")
    def refresh_from_findthatcharity(self, request, queryset):
        """Set the included status of the selected funders to True."""
        org_ids = tuple(queryset.values_list("org_id", flat=True))
        if not org_ids:
            self.message_user(
                request,
                "No funders selected.",
                messages.WARNING,
            )
            return
        do_ftc_funders(
            db_con=os.environ.get("FTC_DB_URL"),
            org_ids=org_ids,
            debug=True,
        )
        do_ftc_finance(
            db_con=os.environ.get("FTC_DB_URL"),
            org_ids=org_ids,
            debug=True,
        )
        self.message_user(
            request,
            f"{queryset.count()} funders refreshed from Find that Charity.",
            messages.SUCCESS,
        )

    @admin.action(description="Mark as included")
    def set_as_included(self, request, queryset):
        """Set the included status of the selected funders to True."""
        queryset.update(included=True)
        self.message_user(
            request,
            f"{queryset.count()} funders have been set as included.",
            messages.SUCCESS,
        )

    @admin.action(description="Mark as excluded")
    def set_as_excluded(self, request, queryset):
        """Set the included status of the selected funders to False."""
        queryset.update(included=False)
        self.message_user(
            request,
            f"{queryset.count()} funders have been set as included.",
            messages.SUCCESS,
        )

    @admin.action(description="Mark as making grants to individuals")
    def set_as_makes_grants_to_individuals(self, request, queryset):
        """Set the makes_grants_to_individuals of the selected funders to True."""
        queryset.update(makes_grants_to_individuals=True)
        self.message_user(
            request,
            f"{queryset.count()} funders have been set as making grants to individuals.",
            messages.SUCCESS,
        )

    @admin.action(description="Mark as not making grants to individuals")
    def set_as_not_makes_grants_to_individuals(self, request, queryset):
        """Set the makes_grants_to_individuals of the selected funders to False."""
        queryset.update(makes_grants_to_individuals=False)
        self.message_user(
            request,
            f"{queryset.count()} funders have been set as not making grants to individuals.",
            messages.SUCCESS,
        )

    def get_actions(self, request):
        actions = super().get_actions(request)

        action_fields = [
            Action("Segment", "segment", FunderSegment, False),
        ]

        return {
            **actions,
            **add_admin_actions(action_fields),
        }

    def handle_file_upload(
        self, file, pk_fields, fields, request, skip_blanks=False, add_new_rows=True
    ):
        result = super().handle_file_upload(
            file, pk_fields, fields, request, skip_blanks, add_new_rows
        )
        # Make sure that all the new funders have a financial year
        query_keys = [
            "Ensure every funder has a funder financial year for the current financial year",
        ]
        queries = {query_name: SQL_QUERIES[query_name] for query_name in query_keys}

        with transaction.atomic(), connection.cursor() as cursor:
            for query_name, query in queries.items():
                cursor.execute(format_query(query))
                messages.add_message(
                    request,
                    messages.INFO,
                    f"Added funder financial year for {cursor.rowcount:,.0f} funders",
                )
        return result
