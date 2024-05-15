from django.contrib import admin
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from django.utils.html import format_html

from ukgrantmaking.admin.csv_upload import CSVUploadModelAdmin
from ukgrantmaking.models import Grant


class CurrencyConverterAdmin(admin.ModelAdmin):
    list_display = ("currency", "date", "rate", "link")
    list_editable = ("rate",)
    list_filter = (
        "currency",
        ("rate", admin.EmptyFieldListFilter),
    )
    ordering = (
        "currency",
        "-date",
    )

    @admin.display(description="Link")
    def link(self, obj):
        return format_html(
            '<a href="https://www.xe.com/currencytables/?from={}&date={}#table-section" target="_blank">XE</a>',
            obj.currency,
            obj.date,
        )


class GrantAmountListFilter(admin.SimpleListFilter):
    title = "Amount awarded"
    parameter_name = "amount_awarded"

    def lookups(self, request, model_admin):
        return [
            ("lt_0", "Below zero"),
            ("0", "Zero"),
            ("lt_1000", "Less than £1,000"),
            ("1000_10000", "£1,001 to £10,000"),
            ("10000_100000", "£10,001 to £100,000"),
            ("100000_1000000", "£100,001 to £1,000,000"),
            ("gt_1000000", "£1,000,001 or more"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "lt_0":
            return queryset.filter(
                amount_awarded__lt=0,
            )
        if self.value() == "0":
            return queryset.filter(
                amount_awarded=0,
            )
        if self.value() == "lt_1000":
            return queryset.filter(
                amount_awarded__gt=0,
                amount_awarded__lte=1_000,
            )
        if self.value() == "1000_10000":
            return queryset.filter(
                amount_awarded__gt=1_000,
                amount_awarded__lte=10_000,
            )
        if self.value() == "10000_100000":
            return queryset.filter(
                amount_awarded__gt=10_000,
                amount_awarded__lte=100_000,
            )
        if self.value() == "100000_1000000":
            return queryset.filter(
                amount_awarded__gt=100_000,
                amount_awarded__lte=1_000_000,
            )
        if self.value() == "gt_1000000":
            return queryset.filter(amount_awarded__gt=1_000_000)


class AwardDateYearFilter(admin.SimpleListFilter):
    title = "Award date year"
    parameter_name = "award_date_year"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        year_list = (
            qs.annotate(y=ExtractYear("award_date"))
            .order_by("y")
            .values_list("y", flat=True)
            .distinct()
        )
        return [(str(y), str(y)) for y in year_list]

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(award_date__year=self.value())
        return queryset

    def get_facet_counts(self, pk_attname, filtered_qs):
        original_value = self.used_parameters.get(self.parameter_name)
        counts = {}
        for i, choice in enumerate(self.lookup_choices):
            self.used_parameters[self.parameter_name] = choice[0]
            counts[f"{i}__c"] = Count(
                pk_attname,
                filter=Q(award_date__year=choice[1]),
            )
        self.used_parameters[self.parameter_name] = original_value
        return counts


class GrantAdmin(CSVUploadModelAdmin):
    list_display = (
        "grant_id",
        "amount_text",
        "award_date",
        "inclusion",
        "funder_text",
        "recipient_text",
        "recipient_type_manual",
        "title",
    )
    date_hierarchy = "award_date"
    list_editable = ("inclusion", "recipient_type_manual")
    raw_id_fields = ("funder",)
    search_fields = (
        "title",
        "description",
        "recipient_organisation_name",
        "recipient_individual_name",
        "funding_organisation_name",
    )
    list_filter = (
        "inclusion",
        "currency",
        AwardDateYearFilter,
        GrantAmountListFilter,
        "recipient_type",
        "recipient_type_manual",
        ("recipient_type_manual", admin.EmptyFieldListFilter),
        "funding_organisation_type",
        "funding_organisation_name",
    )
    readonly_fields = (
        "grant_id",
        "title",
        "description",
        "currency",
        "amount_awarded",
        "amount_awarded_GBP",
        "award_date",
        "planned_dates_duration",
        "planned_dates_startDate",
        "planned_dates_endDate",
        "recipient_organisation_id",
        "recipient_organisation_name",
        "recipient_individual_id",
        "recipient_individual_name",
        "recipient_individual_primary_grant_reason",
        "recipient_individual_secondary_grant_reason",
        "recipient_individual_grant_purpose",
        "recipient_type",
        "funding_organisation_id",
        "funding_organisation_name",
        "funding_organisation_type",
        "regrant_type",
        "location_scope",
        "grant_programme_title",
        "publisher_prefix",
        "publisher_name",
        "license",
    )
    fieldsets = (
        (
            None,
            {
                "fields": [
                    "grant_id",
                    "title",
                    "description",
                    ("amount_awarded", "currency", "amount_awarded_GBP"),
                    "award_date",
                    "inclusion",
                ]
            },
        ),
        (
            "Funder",
            {
                "fields": [
                    ("funding_organisation_id", "funding_organisation_name"),
                    "funding_organisation_type",
                    "funder",
                ]
            },
        ),
        (
            "Recipient",
            {
                "fields": [
                    ("recipient_type", "recipient_type_manual"),
                    ("recipient_organisation_id", "recipient_organisation_name"),
                    ("recipient_individual_id", "recipient_individual_name"),
                    "recipient_individual_primary_grant_reason",
                    "recipient_individual_secondary_grant_reason",
                    "recipient_individual_grant_purpose",
                ]
            },
        ),
        (
            "Planned dates",
            {
                "fields": [
                    "planned_dates_duration",
                    ("planned_dates_startDate", "planned_dates_endDate"),
                ]
            },
        ),
        (
            "Grant details",
            {
                "fields": [
                    ("regrant_type", "regrant_type_manual"),
                    "location_scope",
                    "grant_programme_title",
                ]
            },
        ),
        (
            "Publisher",
            {
                "fields": [
                    "publisher_prefix",
                    "publisher_name",
                    "license",
                ]
            },
        ),
    )

    @admin.display(description="Funder")
    def funder_text(self, obj):
        if obj.funder:
            return obj.funder.name
        return format_html(
            "{}<br>[{}]",
            obj.funding_organisation_name,
            obj.funding_organisation_id,
        )

    @admin.display(description="Recipient")
    def recipient_text(self, obj):
        if obj.recipient_type == Grant.RecipientType.INDIVIDUAL:
            return obj.recipient_individual_name
        return format_html(
            "{}<br>[{}]",
            obj.recipient_organisation_name,
            obj.recipient_organisation_id,
        )

    @admin.display(description="Amount")
    def amount_text(self, obj):
        if obj.currency == "GBP":
            return "£{:,.0f}".format(obj.amount_awarded)
        return "{} {:,.0f}".format(obj.currency, obj.amount_awarded)

    amount_text.admin_order_field = "amount_awarded"


class GrantRecipientAdmin(CSVUploadModelAdmin):
    list_display = (
        "recipient_id",
        "name",
        "type",
    )
    search_fields = ("name", "recipient_id")
    list_filter = ("type", "org_id_schema")
    list_editable = ("type",)


class GrantRecipientYearAdmin(CSVUploadModelAdmin):
    pass
