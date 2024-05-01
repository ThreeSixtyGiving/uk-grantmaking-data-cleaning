from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.lookups import IsNull

from ukgrantmaking.models.funder import FinancialYears, Funder


class FunderYear(models.Model):
    funder = models.ForeignKey(Funder, on_delete=models.CASCADE)
    financial_year_end = models.DateField()
    financial_year_start = models.DateField(null=True, blank=True)
    financial_year = models.CharField(
        max_length=9,
        choices=FinancialYears.choices,
        null=True,
        blank=True,
        db_index=True,
    )

    income_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    income_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    income = models.GeneratedField(
        expression=Coalesce("income_manual", "income_registered"),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )

    spending_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending = models.GeneratedField(
        expression=Coalesce("spending_manual", "spending_registered"),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_charitable_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_charitable_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_charitable = models.GeneratedField(
        expression=Coalesce(
            "spending_charitable_manual", "spending_charitable_registered"
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_grant_making = models.GeneratedField(
        expression=models.Case(
            models.When(
                IsNull(models.F("spending_grant_making_individuals"), False)
                | IsNull(models.F("spending_grant_making_institutions"), False),
                then=(
                    Coalesce(models.F("spending_grant_making_individuals"), 0)
                    + Coalesce(models.F("spending_grant_making_institutions"), 0)
                ),
            )
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_grant_making_individuals_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_individuals_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_individuals = models.GeneratedField(
        expression=Coalesce(
            "spending_grant_making_individuals_manual",
            "spending_grant_making_individuals_registered",
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_grant_making_institutions_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions = models.GeneratedField(
        expression=Coalesce(
            "spending_grant_making_institutions_manual",
            "spending_grant_making_institutions_registered",
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )

    total_net_assets_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    total_net_assets_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    total_net_assets = models.GeneratedField(
        expression=Coalesce("total_net_assets_manual", "total_net_assets_registered"),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )

    funds_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    funds_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    funds = models.GeneratedField(
        expression=Coalesce("funds_manual", "funds_registered"),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    funds_endowment_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    funds_endowment_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    funds_endowment = models.GeneratedField(
        expression=Coalesce("funds_endowment_manual", "funds_endowment_registered"),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    funds_restricted_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    funds_restricted_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    funds_restricted = models.GeneratedField(
        expression=Coalesce("funds_restricted_manual", "funds_restricted_registered"),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    funds_unrestricted_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    funds_unrestricted_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    funds_unrestricted = models.GeneratedField(
        expression=Coalesce(
            "funds_unrestricted_manual", "funds_unrestricted_registered"
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )

    employees_registered = models.IntegerField(null=True, blank=True)
    employees_manual = models.IntegerField(null=True, blank=True)
    employees = models.GeneratedField(
        expression=Coalesce("employees_manual", "employees_registered"),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )

    checked_on = models.DateTimeField(null=True, blank=True)
    checked_by = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["funder", "financial_year_end"]]
        ordering = ["funder", "-financial_year_end"]

    def __str__(self):
        return f"{self.funder.name} ({self.financial_year_end})"

    def save(self, *args, **kwargs):
        if self.financial_year_end:
            if self.financial_year_end.month < 4:
                self.financial_year = f"{self.financial_year_end.year - 1}-{self.financial_year_end.year % 100:02d}"
            else:
                self.financial_year = f"{self.financial_year_end.year}-{(self.financial_year_end.year + 1) % 100:02d}"
        self.funder.save()
        super().save(*args, **kwargs)
