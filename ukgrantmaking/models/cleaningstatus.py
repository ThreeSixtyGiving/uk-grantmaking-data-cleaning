from dataclasses import dataclass
from datetime import date

from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.utils.text import slugify

LOW_THRESHOLD = 0.2
HIGH_THRESHOLD = 0.8


@dataclass
class Meter:
    name: str
    total: int
    value: int

    @property
    def low(self):
        return int(0.5 * self.total)

    @property
    def high(self):
        return int(0.8 * self.total)

    @property
    def optimum(self):
        return self.total

    @property
    def min(self):
        return 0

    @property
    def max(self):
        return self.total


# id (F value): name, group, type
class CleaningStatusType(models.TextChoices):
    GRANT = "Grant", "Grant"
    GRANTMAKER = "Grantmaker", "Grantmaker"


FIELD_GROUPS = [CleaningStatusType.GRANTMAKER, CleaningStatusType.GRANT]
FIELD_DEFINITIONS = [
    ("financial_year_end", "Financial Year End", CleaningStatusType.GRANTMAKER, date),
    ("income", "Income", CleaningStatusType.GRANTMAKER, int),
    ("income_investment", "Income investment", CleaningStatusType.GRANTMAKER, int),
    ("spending", "Spending", CleaningStatusType.GRANTMAKER, int),
    ("spending_investment", "Spending investment", CleaningStatusType.GRANTMAKER, int),
    ("spending_charitable", "Spending charitable", CleaningStatusType.GRANTMAKER, int),
    (
        "spending_grant_making",
        "Spending grant making",
        CleaningStatusType.GRANTMAKER,
        int,
    ),
    (
        "spending_grant_making_individuals",
        "Spending grant making individuals",
        CleaningStatusType.GRANTMAKER,
        int,
    ),
    (
        "spending_grant_making_institutions_charitable",
        "Spending grant making institutions charitable",
        CleaningStatusType.GRANTMAKER,
        int,
    ),
    (
        "spending_grant_making_institutions_noncharitable",
        "Spending grant making institutions noncharitable",
        CleaningStatusType.GRANTMAKER,
        int,
    ),
    (
        "spending_grant_making_institutions_unknown",
        "Spending grant making institutions unknown",
        CleaningStatusType.GRANTMAKER,
        int,
    ),
    (
        "spending_grant_making_institutions",
        "Spending grant making institutions",
        CleaningStatusType.GRANTMAKER,
        int,
    ),
    ("total_net_assets", "Total net assets", CleaningStatusType.GRANTMAKER, int),
    ("funds", "Funds", CleaningStatusType.GRANTMAKER, int),
    ("funds_endowment", "Funds endowment", CleaningStatusType.GRANTMAKER, int),
    ("funds_restricted", "Funds restricted", CleaningStatusType.GRANTMAKER, int),
    ("funds_unrestricted", "Funds unrestricted", CleaningStatusType.GRANTMAKER, int),
    ("employees", "Employees", CleaningStatusType.GRANTMAKER, int),
    ("checked", "Checked", CleaningStatusType.GRANTMAKER, str),
    (
        "funder_financial_year__funder__org_id",
        "Funder ID",
        CleaningStatusType.GRANTMAKER,
        str,
    ),
    (
        "funder_financial_year__funder__name",
        "Funder Name",
        CleaningStatusType.GRANTMAKER,
        str,
    ),
    (
        "funder_financial_year__funder__status",
        "Funder status",
        CleaningStatusType.GRANTMAKER,
        str,
    ),
    (
        "funder_financial_year__funder__date_of_registration",
        "Registration date",
        CleaningStatusType.GRANTMAKER,
        date,
    ),
    (
        "funder_financial_year__funder__date_of_removal",
        "Removal date",
        CleaningStatusType.GRANTMAKER,
        date,
    ),
    (
        "funder_financial_year__funder__active",
        "Funder Active",
        CleaningStatusType.GRANTMAKER,
        bool,
    ),
    (
        "funder_financial_year__funder__latest_year__scaling",
        "Grantmaker size (latest)",
        CleaningStatusType.GRANTMAKER,
        int,
    ),
    (
        "funder_financial_year__scaling",
        "Grantmaker size",
        CleaningStatusType.GRANTMAKER,
        int,
    ),
    (
        "funder_financial_year__tags__tag",
        "Tags",
        CleaningStatusType.GRANTMAKER,
        list[str],
    ),
    ("funder_financial_year__segment", "Segment", CleaningStatusType.GRANTMAKER, str),
    ("funder_financial_year__category", "Category", CleaningStatusType.GRANTMAKER, str),
    (
        "funder_financial_year__included",
        "Included",
        CleaningStatusType.GRANTMAKER,
        bool,
    ),
    (
        "funder_financial_year__makes_grants_to_individuals",
        "Makes grants to individuals",
        CleaningStatusType.GRANTMAKER,
        bool,
    ),
    ("funder_financial_year__checked", "Checked", CleaningStatusType.GRANTMAKER, str),
    (
        "funder_financial_year__checked_on",
        "Checked on",
        CleaningStatusType.GRANTMAKER,
        date,
    ),
    (
        "funder_financial_year__checked_by",
        "Checked by",
        CleaningStatusType.GRANTMAKER,
        str,
    ),
    ("funder_financial_year__notes", "Notes", CleaningStatusType.GRANTMAKER, str),
    (
        "funder_financial_year__date_added",
        "Date added",
        CleaningStatusType.GRANTMAKER,
        date,
    ),
    (
        "funder_financial_year__date_updated",
        "Date updated",
        CleaningStatusType.GRANTMAKER,
        date,
    ),
    ("title", "Title", CleaningStatusType.GRANT, str),
    ("description", "Description", CleaningStatusType.GRANT, str),
    ("currency", "Currency", CleaningStatusType.GRANT, str),
    ("amount_awarded", "Amount awarded", CleaningStatusType.GRANT, int),
    ("amount_awarded_GBP", "Amount awarded GBP", CleaningStatusType.GRANT, int),
    ("award_date", "Award date", CleaningStatusType.GRANT, date),
    ("planned_dates_duration", "Planned dates duration", CleaningStatusType.GRANT, int),
    (
        "planned_dates_startDate",
        "Planned dates startDate",
        CleaningStatusType.GRANT,
        date,
    ),
    ("planned_dates_endDate", "Planned dates endDate", CleaningStatusType.GRANT, date),
    (
        "recipient_organisation_id",
        "Recipient organisation id",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "recipient_organisation_name",
        "Recipient organisation name",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "recipient_individual_id",
        "Recipient individual id",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "recipient_individual_name",
        "Recipient individual name",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "recipient_individual_primary_grant_reason",
        "Recipient individual primary grant reason",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "recipient_individual_secondary_grant_reason",
        "Recipient individual secondary grant reason",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "recipient_individual_grant_purpose",
        "Recipient individual grant purpose",
        CleaningStatusType.GRANT,
        str,
    ),
    ("recipient_type", "Recipient type", CleaningStatusType.GRANT, str),
    (
        "funding_organisation_id",
        "Funding organisation id",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "funding_organisation_name",
        "Funding organisation name",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "funding_organisation_type",
        "Funding organisation type",
        CleaningStatusType.GRANT,
        str,
    ),
    ("regrant_type", "Regrant type", CleaningStatusType.GRANT, str),
    ("location_scope", "Location scope", CleaningStatusType.GRANT, str),
    ("grant_programme_title", "Grant programme title", CleaningStatusType.GRANT, str),
    ("publisher_prefix", "Publisher prefix", CleaningStatusType.GRANT, str),
    ("publisher_name", "Publisher name", CleaningStatusType.GRANT, str),
    ("license", "License", CleaningStatusType.GRANT, str),
    ("recipient_location_rgn", "Recipient location rgn", CleaningStatusType.GRANT, str),
    (
        "recipient_location_ctry",
        "Recipient location ctry",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "beneficiary_location_rgn",
        "Beneficiary location rgn",
        CleaningStatusType.GRANT,
        str,
    ),
    (
        "beneficiary_location_ctry",
        "Beneficiary location ctry",
        CleaningStatusType.GRANT,
        str,
    ),
    ("funder", "Funder", CleaningStatusType.GRANT, str),
    ("recipient", "Recipient", CleaningStatusType.GRANT, str),
    ("recipient_type_manual", "Recipient type manual", CleaningStatusType.GRANT, str),
    ("inclusion", "Inclusion", CleaningStatusType.GRANT, str),
    ("notes", "Notes", CleaningStatusType.GRANT, str),
    ("checked_by", "Checked by", CleaningStatusType.GRANT, str),
    ("annual_amount", "Annual amount", CleaningStatusType.GRANT, int),
]
FIELD_CHOICES = {
    field_group: {
        field[0]: field[1] for field in FIELD_DEFINITIONS if field[2] == field_group
    }
    for field_group in FIELD_GROUPS
}
FIELD_TYPES = {(field[2], field[0]): field[3] for field in FIELD_DEFINITIONS}
FIELD_NAMES = {field[0]: field[1] for field in FIELD_DEFINITIONS}


class Comparison(models.TextChoices):
    EQUAL = "Equal", "Equal"
    NOT_EQUAL = "Not Equal", "Not Equal"
    GREATER_THAN = "Greater Than", "Greater Than"
    LESS_THAN = "Less Than", "Less Than"
    GREATER_THAN_OR_EQUAL = "Greater Than or Equal", "Greater Than or Equal"
    LESS_THAN_OR_EQUAL = "Less Than or Equal", "Less Than or Equal"
    CONTAINS = "Contains", "Contains"
    NOT_CONTAINS = "Not Contains", "Not Contains"
    STARTS_WITH = "Starts With", "Starts With"
    ENDS_WITH = "Ends With", "Ends With"
    IS_NULL = "Is Null", "Is Null"
    IS_NOT_NULL = "Is Not Null", "Is Not Null"
    IS_TRUE = "Is True", "Is True"
    IS_FALSE = "Is False", "Is False"


AVAILABLE_COMPARISONS = {
    str: [
        Comparison.EQUAL,
        Comparison.NOT_EQUAL,
        Comparison.CONTAINS,
        Comparison.NOT_CONTAINS,
        Comparison.STARTS_WITH,
        Comparison.ENDS_WITH,
        Comparison.IS_NULL,
        Comparison.IS_NOT_NULL,
    ],
    bool: [
        Comparison.EQUAL,
        Comparison.NOT_EQUAL,
        Comparison.IS_TRUE,
        Comparison.IS_FALSE,
    ],
    int: [
        Comparison.EQUAL,
        Comparison.NOT_EQUAL,
        Comparison.GREATER_THAN,
        Comparison.LESS_THAN,
        Comparison.GREATER_THAN_OR_EQUAL,
        Comparison.LESS_THAN_OR_EQUAL,
        Comparison.IS_NULL,
        Comparison.IS_NOT_NULL,
    ],
    date: [
        Comparison.EQUAL,
        Comparison.NOT_EQUAL,
        Comparison.GREATER_THAN,
        Comparison.LESS_THAN,
        Comparison.GREATER_THAN_OR_EQUAL,
        Comparison.LESS_THAN_OR_EQUAL,
        Comparison.IS_NULL,
        Comparison.IS_NOT_NULL,
    ],
    list[str]: [
        Comparison.EQUAL,
        Comparison.NOT_EQUAL,
        Comparison.CONTAINS,
        Comparison.NOT_CONTAINS,
        Comparison.IS_NULL,
        Comparison.IS_NOT_NULL,
    ],
}


class CleaningOperator(models.TextChoices):
    AND = "AND", "AND"
    OR = "OR", "OR"


class CleaningStatus(models.Model):
    class SortOrder(models.TextChoices):
        ASC = "A", "Ascending"
        DESC = "D", "Descending"

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=50,
        choices=CleaningStatusType.choices,
        default=CleaningStatusType.GRANTMAKER,
    )
    n = models.IntegerField(
        default=50,
        help_text="Number of records to return. Set to 0 to return all records.",
    )
    sort_by = models.CharField(
        max_length=255,
        choices=FIELD_CHOICES,
        default="funder_financial_year__funder__latest_year__scaling",
    )
    sort_order = models.CharField(
        max_length=1,
        choices=SortOrder.choices,
        default=SortOrder.DESC,
    )
    date_added = models.DateTimeField(auto_now_add=True, db_index=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    def __init__(self, *args, **kwargs):
        self._query_results = {}
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return slugify(self.name)

    class Meta:
        verbose_name = "Cleaning check"
        verbose_name_plural = "Cleaning checks"
        ordering = ["name"]

    @property
    def sort_by_name(self) -> str:
        sort_by = FIELD_NAMES.get(self.sort_by, self.sort_by)
        if sort_by:
            return f"{sort_by} ({self.SortOrder(self.sort_order).label})"

    @property
    def queries_qs(self):
        return self.cleaningstatusquery_set.order_by("order")

    @property
    def active_queries_qs(self):
        return self.queries_qs.filter(active=True)

    def run(self, qs, exclude_cleaned=False):
        query_hash = hash((self.pk, qs.query.__str__(), exclude_cleaned))

        if query_hash in self._query_results:
            return self._query_results[query_hash]

        previous_query: models.Q = None
        for query in self.active_queries_qs:
            query_filter = query.get_filter(qs, self.type)
            if not previous_query:
                previous_query = query_filter
            elif query.operator == CleaningOperator.AND:
                # if we have a previous query, add it to the main query
                qs = qs.filter(previous_query)
                previous_query = query_filter
            elif query.operator == CleaningOperator.OR:
                # if we have a previous query, the new previous query is the previous query OR the new query
                previous_query = previous_query | query_filter

        # add the last query to the main query
        if previous_query:
            qs = qs.filter(previous_query)

        if exclude_cleaned:
            if self.type == CleaningStatusType.GRANTMAKER:
                qs = qs.filter(
                    ~models.Q(
                        funder_financial_year__checked="Checked",
                        funder_financial_year__checked__isnull=False,
                    )
                )

        if self.sort_by:
            if self.sort_order == self.SortOrder.DESC:
                qs = qs.order_by(models.F(self.sort_by).desc(nulls_last=True))
            else:
                qs = qs.order_by(models.F(self.sort_by).asc(nulls_last=True))
            qs = qs.distinct(self.sort_by, "id")
        else:
            qs = qs.distinct("id")
        if self.n > 0:
            qs = qs[: self.n]
        self._query_results[query_hash] = list(qs)
        return self._query_results[query_hash]

    def get_status(self, qs):
        results = self.run(qs)
        total = len(results)
        if self.type == CleaningStatusType.GRANTMAKER:
            checked = len(
                [r for r in results if r.funder_financial_year.checked == "Checked"]
            )
            return [
                Meter(
                    **{
                        "name": "Checked",
                        "total": total,
                        "value": checked,
                    }
                ),
                # Meter(
                #     **{
                #         "name": "Checked segment",
                #         "total": total,
                #         "value": self.run(
                #             qs.filter(funder_financial_year__funder__status="Checked")
                #         ).count(),
                #     }
                # ),
            ]
        raise NotImplementedError(f"Type {self.type} not implemented")

    def get_absolute_url(self):
        return reverse("grantmakers:task_detail", kwargs={"task_id": self.pk})

    def get_csv_url(self):
        return reverse("grantmakers:task_detail_csv", kwargs={"task_id": self.pk})


class CleaningStatusQuery(models.Model):
    cleaning_status = models.ForeignKey(CleaningStatus, on_delete=models.CASCADE)
    operator = models.CharField(
        max_length=50, choices=CleaningOperator.choices, default=CleaningOperator.AND
    )
    field = models.CharField(max_length=255, choices=FIELD_CHOICES)
    comparison = models.CharField(
        max_length=50, choices=Comparison.choices, default=Comparison.EQUAL
    )
    value = models.CharField(max_length=50, null=True, blank=True)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(
        default=0, blank=False, null=False, db_index=True
    )

    date_added = models.DateTimeField(auto_now_add=True, db_index=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.operator} {FIELD_NAMES.get(self.field, self.field)} {self.comparison_str()}"

    def clean(self):
        if self.field not in FIELD_CHOICES[self.cleaning_status.type]:
            raise ValidationError(
                f"Field {self.field} not available for type {self.cleaning_status.type}"
            )

        field_type = FIELD_TYPES[self.cleaning_status.type, self.field]
        if self.comparison not in AVAILABLE_COMPARISONS[field_type]:
            raise ValidationError(
                f"Comparison {self.comparison} not available for field {self.field}"
            )

        if not self.value and self.comparison not in [
            Comparison.IS_NULL,
            Comparison.IS_NOT_NULL,
            Comparison.IS_FALSE,
            Comparison.IS_TRUE,
        ]:
            raise ValidationError(f"Value required for comparison {self.comparison}")

    def get_filter(self, qs, status_type) -> models.Q:
        field_type = FIELD_TYPES[status_type, self.field]
        if self.comparison not in AVAILABLE_COMPARISONS[field_type]:
            raise ValueError(
                f"Comparison {self.comparison} not available for field {self.field}"
            )

        if self.comparison == Comparison.IS_NULL:
            return models.Q(**{f"{self.field}__isnull": True})
        if self.comparison == Comparison.IS_NOT_NULL:
            return models.Q(**{f"{self.field}__isnull": False})
        if self.comparison == Comparison.CONTAINS:
            return models.Q(**{f"{self.field}__icontains": self.value})
        if self.comparison == Comparison.NOT_CONTAINS:
            return ~models.Q(**{f"{self.field}__icontains": self.value})
        if self.comparison == Comparison.EQUAL:
            return models.Q(**{self.field: self.value})
        if self.comparison == Comparison.NOT_EQUAL:
            return models.Q(**{self.field: self.value})
        if self.comparison == Comparison.GREATER_THAN:
            return models.Q(**{f"{self.field}__gt": self.value})
        if self.comparison == Comparison.LESS_THAN:
            return models.Q(**{f"{self.field}__lt": self.value})
        if self.comparison == Comparison.GREATER_THAN_OR_EQUAL:
            return models.Q(**{f"{self.field}__gte": self.value})
        if self.comparison == Comparison.LESS_THAN_OR_EQUAL:
            return models.Q(**{f"{self.field}__lte": self.value})
        if self.comparison == Comparison.STARTS_WITH:
            return models.Q(**{f"{self.field}__startswith": self.value})
        if self.comparison == Comparison.ENDS_WITH:
            return models.Q(**{f"{self.field}__endswith": self.value})
        if self.comparison == Comparison.IS_TRUE:
            return models.Q(**{self.field: True})
        if self.comparison == Comparison.IS_FALSE:
            return models.Q(**{self.field: False})

        raise NotImplementedError(f"Comparison {self.comparison} not implemented")

    def comparison_str(self):
        if self.comparison == Comparison.IS_NULL:
            return "is null"
        if self.comparison == Comparison.IS_NOT_NULL:
            return "is not null"
        if self.comparison == Comparison.CONTAINS:
            return f"contains '{self.value}'"
        if self.comparison == Comparison.NOT_CONTAINS:
            return f"doesn't contain '{self.value}'"
        if self.comparison == Comparison.EQUAL:
            return f"= '{self.value}'"
        if self.comparison == Comparison.NOT_EQUAL:
            return f"!= '{self.value}'"
        if self.comparison == Comparison.GREATER_THAN:
            return f"> {self.value}"
        if self.comparison == Comparison.LESS_THAN:
            return f"< {self.value}"
        if self.comparison == Comparison.GREATER_THAN_OR_EQUAL:
            return f">= {self.value}"
        if self.comparison == Comparison.LESS_THAN_OR_EQUAL:
            return f"<= {self.value}"
        if self.comparison == Comparison.STARTS_WITH:
            return f"starts with '{self.value}'"
        if self.comparison == Comparison.ENDS_WITH:
            return f"ends with '{self.value}'"
        if self.comparison == Comparison.IS_TRUE:
            return "is True"
        if self.comparison == Comparison.IS_FALSE:
            return "is False"

    class Meta:
        ordering = ["cleaning_status", "order"]
