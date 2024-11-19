from dataclasses import dataclass

from django.db import models
from django.urls import reverse

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


FIELD_CHOICES = {
    "Grantmaker": {
        "financial_year_end": "Financial Year End",
        "income": "Income",
        "income_investment": "Income investment",
        "spending": "Spending",
        "spending_investment": "Spending investment",
        "spending_charitable": "Spending charitable",
        "spending_grant_making": "Spending grant making",
        "spending_grant_making_individuals": "Spending grant making individuals",
        "spending_grant_making_institutions_charitable": "Spending grant making institutions charitable",
        "spending_grant_making_institutions_noncharitable": "Spending grant making institutions noncharitable",
        "spending_grant_making_institutions_unknown": "Spending grant making institutions unknown",
        "spending_grant_making_institutions": "Spending grant making institutions",
        "total_net_assets": "Total net assets",
        "funds": "Funds",
        "funds_endowment": "Funds endowment",
        "funds_restricted": "Funds restricted",
        "funds_unrestricted": "Funds unrestricted",
        "employees": "Employees",
        "checked": "Checked",
        "funder_financial_year__funder__org_id": "Funder ID",
        "funder_financial_year__funder__name": "Funder Name",
        "funder_financial_year__funder__status": "Funder status",
        "funder_financial_year__scaling": "Grantmaker size",
        "funder_financial_year__tags": "Tags",
        "funder_financial_year__segment": "Segment",
        "funder_financial_year__included": "Included",
        "funder_financial_year__makes_grants_to_individuals": "Makes grants to individuals",
        "funder_financial_year__checked": "Checked",
        "funder_financial_year__checked_on": "Checked on",
        "funder_financial_year__checked_by": "Checked by",
        "funder_financial_year__notes": "Notes",
        "funder_financial_year__date_added": "Date added",
        "funder_financial_year__date_updated": "Date updated",
    },
    "Grant": {
        "title": "Title",
        "description": "Description",
        "currency": "Currency",
        "amount_awarded": "Amount awarded",
        "amount_awarded_GBP": "Amount awarded GBP",
        "award_date": "Award date",
        "planned_dates_duration": "Planned dates duration",
        "planned_dates_startDate": "Planned dates startDate",
        "planned_dates_endDate": "Planned dates endDate",
        "recipient_organisation_id": "Recipient organisation id",
        "recipient_organisation_name": "Recipient organisation name",
        "recipient_individual_id": "Recipient individual id",
        "recipient_individual_name": "Recipient individual name",
        "recipient_individual_primary_grant_reason": "Recipient individual primary grant reason",
        "recipient_individual_secondary_grant_reason": "Recipient individual secondary grant reason",
        "recipient_individual_grant_purpose": "Recipient individual grant purpose",
        "recipient_type": "Recipient type",
        "funding_organisation_id": "Funding organisation id",
        "funding_organisation_name": "Funding organisation name",
        "funding_organisation_type": "Funding organisation type",
        "regrant_type": "Regrant type",
        "location_scope": "Location scope",
        "grant_programme_title": "Grant programme title",
        "publisher_prefix": "Publisher prefix",
        "publisher_name": "Publisher name",
        "license": "License",
        "recipient_location_rgn": "Recipient location rgn",
        "recipient_location_ctry": "Recipient location ctry",
        "beneficiary_location_rgn": "Beneficiary location rgn",
        "beneficiary_location_ctry": "Beneficiary location ctry",
        "funder": "Funder",
        "recipient": "Recipient",
        "recipient_type_manual": "Recipient type manual",
        "inclusion": "Inclusion",
        "notes": "Notes",
        "checked_by": "Checked by",
        "annual_amount": "Annual amount",
    },
}


class CleaningStatus(models.Model):
    class CleaningStatusType(models.TextChoices):
        GRANT = "Grant", "Grant"
        GRANTMAKER = "Grantmaker", "Grantmaker"

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
    n = models.IntegerField(default=50)
    sort_by = models.CharField(
        max_length=50,
        choices=FIELD_CHOICES,
        default="funder_financial_year__scaling",
    )
    sort_order = models.CharField(
        max_length=1,
        choices=SortOrder.choices,
        default=SortOrder.DESC,
    )
    date_added = models.DateTimeField(auto_now_add=True, db_index=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cleaning check"
        verbose_name_plural = "Cleaning checks"
        ordering = ["name"]

    def run(self, qs):
        for query in self.cleaningstatusquery_set.filter(active=True):
            qs = query.get_filter(qs)
        if self.sort_by:
            if self.sort_order == self.SortOrder.DESC:
                qs = qs.order_by(models.F(self.sort_by).desc(nulls_last=True))
            else:
                qs = qs.order_by(models.F(self.sort_by).asc(nulls_last=True))
        return qs[: self.n]

    def get_status(self, qs):
        total = self.run(qs).count()
        if self.type == self.CleaningStatusType.GRANTMAKER:
            return [
                Meter(
                    **{
                        "name": "Checked",
                        "total": total,
                        "value": self.run(
                            qs.filter(funder_financial_year__checked="Checked")
                        ).count(),
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


class CleaningStatusQuery(models.Model):
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

    cleaning_status = models.ForeignKey(CleaningStatus, on_delete=models.CASCADE)
    field = models.CharField(max_length=50, choices=FIELD_CHOICES)
    comparison = models.CharField(
        max_length=50, choices=Comparison.choices, default=Comparison.EQUAL
    )
    value = models.CharField(max_length=50)
    active = models.BooleanField(default=True)

    date_added = models.DateTimeField(auto_now_add=True, db_index=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    def get_filter(self, qs):
        if self.comparison == self.Comparison.IS_NULL:
            return qs.filter(**{f"{self.field}__isnull": True})
        if self.comparison == self.Comparison.IS_NOT_NULL:
            return qs.filter(**{f"{self.field}__isnull": False})
        if self.comparison == self.Comparison.CONTAINS:
            return qs.filter(**{f"{self.field}__icontains": self.value})
        if self.comparison == self.Comparison.NOT_CONTAINS:
            return qs.exclude(**{f"{self.field}__icontains": self.value})
        if self.comparison == self.Comparison.EQUAL:
            return qs.filter(**{self.field: self.value})
        if self.comparison == self.Comparison.NOT_EQUAL:
            return qs.filter(**{self.field: self.value})
        if self.comparison == self.Comparison.GREATER_THAN:
            return qs.filter(**{f"{self.field}__gt": self.value})
        if self.comparison == self.Comparison.LESS_THAN:
            return qs.filter(**{f"{self.field}__lt": self.value})
        if self.comparison == self.Comparison.GREATER_THAN_OR_EQUAL:
            return qs.filter(**{f"{self.field}__gte": self.value})
        if self.comparison == self.Comparison.LESS_THAN_OR_EQUAL:
            return qs.filter(**{f"{self.field}__lte": self.value})
        if self.comparison == self.Comparison.STARTS_WITH:
            return qs.filter(**{f"{self.field}__startswith": self.value})
        if self.comparison == self.Comparison.ENDS_WITH:
            return qs.filter(**{f"{self.field}__endswith": self.value})

        raise NotImplementedError(f"Comparison {self.comparison} not implemented")
