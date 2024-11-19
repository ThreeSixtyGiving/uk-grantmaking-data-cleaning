from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce
from markdownx.models import MarkdownxField

from ukgrantmaking.models.funder_utils import FunderSegment, RecordStatus


class FunderFinancialYear(models.Model):
    funder = models.ForeignKey(
        "Funder", on_delete=models.CASCADE, related_name="funder_financial_years"
    )
    financial_year = models.ForeignKey(
        "FinancialYear", on_delete=models.CASCADE, related_name="funder_financial_years"
    )

    tags = models.ManyToManyField("FunderTag", blank=True)
    segment = models.CharField(
        max_length=50,
        choices=FunderSegment.choices,
        default=FunderSegment.GENERAL_GRANTMAKER,
        null=True,
        blank=True,
        db_index=True,
    )
    included = models.BooleanField(
        default=True,
        db_index=True,
    )
    makes_grants_to_individuals = models.BooleanField(
        default=False,
        db_index=True,
    )

    # fields generated from financial years
    income = models.BigIntegerField(null=True, blank=True, editable=False)
    income_investment = models.BigIntegerField(null=True, blank=True, editable=False)
    spending = models.BigIntegerField(null=True, blank=True, editable=False)
    spending_investment = models.BigIntegerField(null=True, blank=True, editable=False)
    spending_charitable = models.BigIntegerField(null=True, blank=True, editable=False)
    spending_grant_making = models.BigIntegerField(
        null=True, blank=True, editable=False
    )
    spending_grant_making_individuals = models.BigIntegerField(
        null=True, blank=True, editable=False
    )
    spending_grant_making_institutions_charitable = models.BigIntegerField(
        null=True, blank=True, editable=False
    )
    spending_grant_making_institutions_noncharitable = models.BigIntegerField(
        null=True, blank=True, editable=False
    )
    spending_grant_making_institutions_unknown = models.BigIntegerField(
        null=True, blank=True, editable=False
    )
    spending_grant_making_institutions = models.BigIntegerField(
        null=True, blank=True, editable=False
    )
    total_net_assets = models.BigIntegerField(null=True, blank=True, editable=False)
    funds = models.BigIntegerField(null=True, blank=True, editable=False)
    funds_endowment = models.BigIntegerField(null=True, blank=True, editable=False)
    funds_restricted = models.BigIntegerField(null=True, blank=True, editable=False)
    funds_unrestricted = models.BigIntegerField(null=True, blank=True, editable=False)
    employees = models.BigIntegerField(null=True, blank=True, editable=False)

    scaling = models.GeneratedField(
        expression=Coalesce(
            models.F("spending_grant_making"),
            models.F("spending_charitable"),
            models.F("spending"),
            0,
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )

    checked = models.CharField(
        max_length=50,
        choices=RecordStatus.choices,
        null=True,
        blank=True,
        db_index=True,
        default=RecordStatus.UNCHECKED,
    )
    checked_on = models.DateTimeField(null=True, blank=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    notes = MarkdownxField(null=True, blank=True)
    date_added = models.DateTimeField(
        auto_now_add=True, db_index=True, null=True, blank=True
    )
    date_updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = [["funder", "financial_year"]]

    def __str__(self):
        return f"{self.funder.name} ({self.financial_year.fy})"

    def update_fields(self):
        summed_fields = [
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
        ]
        latest_fields = [
            "total_net_assets",
            "funds",
            "funds_endowment",
            "funds_restricted",
            "funds_unrestricted",
            "employees",
        ]
        fys = list(
            self.funder_years.order_by("-financial_year_end").values(
                *(summed_fields + latest_fields)
            )
        )
        if fys:
            for field in summed_fields:
                values = [fy[field] for fy in fys if fy[field] is not None]
                if values:
                    setattr(self, field, sum(values))
                else:
                    setattr(self, field, None)
            for field in latest_fields:
                setattr(self, field, fys[0][field])
        else:
            for field in summed_fields:
                setattr(self, field, None)
            for field in latest_fields:
                setattr(self, field, None)
