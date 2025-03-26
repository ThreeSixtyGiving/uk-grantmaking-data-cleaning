from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.functions import Cast, Coalesce
from django.db.models.lookups import IsNull

from ukgrantmaking.models.funder_financial_year import FunderFinancialYear
from ukgrantmaking.models.funder_utils import EditableField


class FunderYear(models.Model):
    financial_year_end = models.DateField(db_index=True)
    financial_year_start = models.DateField(null=True, blank=True)
    funder_financial_year = models.ForeignKey(
        FunderFinancialYear,
        on_delete=models.CASCADE,
        related_name="funder_years",
        null=True,
        blank=True,
    )
    new_funder_financial_year = models.ForeignKey(
        FunderFinancialYear,
        on_delete=models.CASCADE,
        related_name="original_funder_years",
        null=True,
        blank=True,
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

    income_investment_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    income_investment_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    income_investment = models.GeneratedField(
        expression=Coalesce("income_investment_manual", "income_investment_registered"),
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
    spending_investment_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_investment_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_investment = models.GeneratedField(
        expression=Coalesce(
            "spending_investment_manual", "spending_investment_registered"
        ),
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
        expression=(
            models.Case(
                models.When(
                    IsNull(
                        Coalesce(
                            "spending_grant_making_institutions_charitable_manual",
                            "spending_grant_making_institutions_noncharitable_manual",
                            "spending_grant_making_institutions_unknown_manual",
                            output_field=models.BigIntegerField(),
                        ),
                        False,
                    ),
                    then=models.ExpressionWrapper(
                        Coalesce(
                            "spending_grant_making_institutions_charitable_manual",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                        + Coalesce(
                            "spending_grant_making_institutions_noncharitable_manual",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                        + Coalesce(
                            "spending_grant_making_institutions_unknown_manual",
                            0,
                            output_field=models.BigIntegerField(),
                        ),
                        output_field=models.BigIntegerField(),
                    ),
                ),
                models.When(
                    IsNull(
                        Cast(
                            "spending_grant_making_institutions_main_manual",
                            output_field=models.BigIntegerField(),
                        ),
                        False,
                    ),
                    then=(
                        Coalesce(
                            "spending_grant_making_institutions_main_manual",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                    ),
                ),
                models.When(
                    IsNull(
                        Coalesce(
                            "spending_grant_making_institutions_charitable_registered",
                            "spending_grant_making_institutions_noncharitable_registered",
                            "spending_grant_making_institutions_unknown_registered",
                            output_field=models.BigIntegerField(),
                        ),
                        False,
                    ),
                    then=models.ExpressionWrapper(
                        Coalesce(
                            "spending_grant_making_institutions_charitable_registered",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                        + Coalesce(
                            "spending_grant_making_institutions_noncharitable_registered",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                        + Coalesce(
                            "spending_grant_making_institutions_unknown_registered",
                            0,
                            output_field=models.BigIntegerField(),
                        ),
                        output_field=models.BigIntegerField(),
                    ),
                ),
                models.When(
                    IsNull(
                        Cast(
                            "spending_grant_making_institutions_main_registered",
                            output_field=models.BigIntegerField(),
                        ),
                        False,
                    ),
                    then=(
                        Coalesce(
                            "spending_grant_making_institutions_main_registered",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                    ),
                ),
                models.When(
                    IsNull(
                        Coalesce(
                            "spending_grant_making_institutions_charitable_360Giving",
                            "spending_grant_making_institutions_noncharitable_360Giving",
                            "spending_grant_making_institutions_unknown_360Giving",
                            output_field=models.BigIntegerField(),
                        ),
                        False,
                    ),
                    then=models.ExpressionWrapper(
                        Coalesce(
                            "spending_grant_making_institutions_charitable_360Giving",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                        + Coalesce(
                            "spending_grant_making_institutions_noncharitable_360Giving",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                        + Coalesce(
                            "spending_grant_making_institutions_unknown_360Giving",
                            0,
                            output_field=models.BigIntegerField(),
                        ),
                        output_field=models.BigIntegerField(),
                    ),
                ),
                models.When(
                    IsNull(
                        Cast(
                            "spending_grant_making_institutions_main_360Giving",
                            output_field=models.BigIntegerField(),
                        ),
                        False,
                    ),
                    then=(
                        Coalesce(
                            "spending_grant_making_institutions_main_360Giving",
                            0,
                            output_field=models.BigIntegerField(),
                        )
                    ),
                ),
                models.When(
                    IsNull(
                        Coalesce(
                            "spending_grant_making_individuals_manual",
                            "spending_grant_making_individuals_registered",
                            "spending_grant_making_individuals_360Giving",
                            output_field=models.BigIntegerField(),
                        ),
                        False,
                    ),
                    then=0,
                ),
            )
            + Coalesce(
                "spending_grant_making_individuals_manual",
                "spending_grant_making_individuals_registered",
                "spending_grant_making_individuals_360Giving",
                0,
                output_field=models.BigIntegerField(),
            )
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_grant_making_individuals_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_individuals_360Giving = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_individuals_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_individuals = models.GeneratedField(
        expression=Coalesce(
            "spending_grant_making_individuals_manual",
            "spending_grant_making_individuals_registered",
            "spending_grant_making_individuals_360Giving",
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_grant_making_institutions_charitable_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_charitable_360Giving = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_charitable_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_charitable = models.GeneratedField(
        expression=Coalesce(
            "spending_grant_making_institutions_charitable_manual",
            "spending_grant_making_institutions_charitable_registered",
            "spending_grant_making_institutions_charitable_360Giving",
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_grant_making_institutions_noncharitable_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_noncharitable_360Giving = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_noncharitable_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_noncharitable = models.GeneratedField(
        expression=Coalesce(
            "spending_grant_making_institutions_noncharitable_manual",
            "spending_grant_making_institutions_noncharitable_registered",
            "spending_grant_making_institutions_noncharitable_360Giving",
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_grant_making_institutions_unknown_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_unknown_360Giving = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_unknown_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_unknown = models.GeneratedField(
        expression=Coalesce(
            "spending_grant_making_institutions_unknown_manual",
            "spending_grant_making_institutions_unknown_registered",
            "spending_grant_making_institutions_unknown_360Giving",
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    spending_grant_making_institutions_main_registered = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_main_360Giving = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_main_manual = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    spending_grant_making_institutions_main = models.GeneratedField(
        expression=Coalesce(
            "spending_grant_making_institutions_main_manual",
            "spending_grant_making_institutions_main_registered",
            "spending_grant_making_institutions_main_360Giving",
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    # spending_grant_making_institutions priority order:
    #
    spending_grant_making_institutions = models.GeneratedField(
        expression=models.Case(
            models.When(
                IsNull(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_manual",
                        "spending_grant_making_institutions_noncharitable_manual",
                        "spending_grant_making_institutions_unknown_manual",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                ),
                then=models.ExpressionWrapper(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_manual",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_noncharitable_manual",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_unknown_manual",
                        0,
                        output_field=models.BigIntegerField(),
                    ),
                    output_field=models.BigIntegerField(),
                ),
            ),
            models.When(
                IsNull(
                    Cast(
                        "spending_grant_making_institutions_main_manual",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                ),
                then=(
                    Coalesce(
                        "spending_grant_making_institutions_main_manual",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                ),
            ),
            models.When(
                IsNull(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_registered",
                        "spending_grant_making_institutions_noncharitable_registered",
                        "spending_grant_making_institutions_unknown_registered",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                ),
                then=models.ExpressionWrapper(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_registered",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_noncharitable_registered",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_unknown_registered",
                        0,
                        output_field=models.BigIntegerField(),
                    ),
                    output_field=models.BigIntegerField(),
                ),
            ),
            models.When(
                IsNull(
                    Cast(
                        "spending_grant_making_institutions_main_registered",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                ),
                then=(
                    Coalesce(
                        "spending_grant_making_institutions_main_registered",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                ),
            ),
            models.When(
                IsNull(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_360Giving",
                        "spending_grant_making_institutions_noncharitable_360Giving",
                        "spending_grant_making_institutions_unknown_360Giving",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                ),
                then=models.ExpressionWrapper(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_noncharitable_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_unknown_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    ),
                    output_field=models.BigIntegerField(),
                ),
            ),
            models.When(
                IsNull(
                    Cast(
                        "spending_grant_making_institutions_main_360Giving",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                ),
                then=(
                    Coalesce(
                        "spending_grant_making_institutions_main_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                ),
            ),
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
    employees_permanent_registered = models.IntegerField(null=True, blank=True)
    employees_permanent_manual = models.IntegerField(null=True, blank=True)
    employees_permanent = models.GeneratedField(
        expression=Coalesce(
            "employees_permanent_manual", "employees_permanent_registered"
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    employees_fixedterm_registered = models.IntegerField(null=True, blank=True)
    employees_fixedterm_manual = models.IntegerField(null=True, blank=True)
    employees_fixedterm = models.GeneratedField(
        expression=Coalesce(
            "employees_fixedterm_manual", "employees_fixedterm_registered"
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
    employees_selfemployed_registered = models.IntegerField(null=True, blank=True)
    employees_selfemployed_manual = models.IntegerField(null=True, blank=True)
    employees_selfemployed = models.GeneratedField(
        expression=Coalesce(
            "employees_selfemployed_manual", "employees_selfemployed_registered"
        ),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )

    checked_on = models.DateTimeField(null=True, blank=True)
    checked_by = models.CharField(max_length=255, null=True, blank=True)
    notes = GenericRelation("FunderNote")
    date_added = models.DateTimeField(auto_now_add=True, db_index=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["funder_financial_year", "-financial_year_end"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "funder_financial_year",
                    "financial_year_end",
                ],
                name="unique_funder_year",
            ),
        ]

    def __str__(self):
        if self.new_funder_financial_year:
            return f"{self.new_funder_financial_year.funder.name} ({self.financial_year_end})"
        return f"{self.funder_financial_year.funder.name} ({self.financial_year_end})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.funder_financial_year.update_fields()
        self.funder_financial_year.save()
        if self.new_funder_financial_year:
            self.new_funder_financial_year.update_fields()
            self.new_funder_financial_year.save()

    def editable_fields(self) -> list[EditableField]:
        fields = [
            "income",
            "income_investment",
            "spending",
            "spending_investment",
            "spending_grant_making_individuals",
            # "spending_grant_making_institutions",
            "spending_grant_making_institutions_charitable",
            "spending_grant_making_institutions_noncharitable",
            "spending_grant_making_institutions_unknown",
            "spending_grant_making_institutions_main",
            # "total_net_assets",
            # "funds",
            "funds_endowment",
            "funds_restricted",
            "funds_unrestricted",
            "employees",
            "employees_permanent",
            "employees_fixedterm",
            "employees_selfemployed",
        ]
        field_labels = {
            "spending_grant_making_institutions_charitable": "Grant to institutions (charitable)",
            "spending_grant_making_institutions_noncharitable": "Grant to institutions (noncharitable)",
            "spending_grant_making_institutions_unknown": "Grant to institutions (unknown)",
            "spending_grant_making_institutions_main": "Grant to institutions (main/Part B)",
        }
        field_return = []
        for field in fields:
            field_obj = EditableField(
                name=field,
                label=field_labels.get(field, self._meta.get_field(field).verbose_name),
                registered=None,
                tsg=None,
                manual=None,
            )
            for i in ["registered", "360Giving", "manual"]:
                try:
                    field_obj.set_field(i, self._meta.get_field(f"{field}_{i}"))
                except FieldDoesNotExist:
                    pass
            field_return.append(field_obj)
        return field_return

    @property
    def account_url(self):
        if self.funder_financial_year.funder_id.startswith("GB-CHC-"):
            return "https://ccew.dkane.net/charity/{}/accounts/{}".format(
                self.funder_financial_year.funder_id.replace("GB-CHC-", ""),
                self.financial_year_end,
            )
        return None
