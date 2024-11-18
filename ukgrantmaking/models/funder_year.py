from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.lookups import IsNull
from markdownx.models import MarkdownxField

from ukgrantmaking.models.funder_utils import EditableField, FunderSegment, RecordStatus


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
                setattr(
                    self, field, sum([fy[field] for fy in fys if fy[field] is not None])
                )
            for field in latest_fields:
                setattr(self, field, fys[0][field])
        else:
            for field in summed_fields:
                setattr(self, field, None)
            for field in latest_fields:
                setattr(self, field, None)

    def save(self, *args, **kwargs):
        if self.financial_year.current:
            self.segment = self.funder.segment
            self.included = self.funder.included
            self.makes_grants_to_individuals = self.funder.makes_grants_to_individuals

        if self.pk:
            if self.financial_year.current:
                self.tags.set(self.funder.tags.all())
            self.update_fields()

        super().save(*args, **kwargs)


class FunderYear(models.Model):
    financial_year_end = models.DateField()
    financial_year_start = models.DateField(null=True, blank=True)
    funder_financial_year = models.ForeignKey(
        FunderFinancialYear,
        on_delete=models.CASCADE,
        related_name="funder_years",
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
        expression=models.Case(
            models.When(
                IsNull(
                    Coalesce(
                        "spending_grant_making_individuals_manual",
                        "spending_grant_making_individuals_registered",
                        "spending_grant_making_individuals_360Giving",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                )
                | IsNull(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_manual",
                        "spending_grant_making_institutions_charitable_registered",
                        "spending_grant_making_institutions_charitable_360Giving",
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_noncharitable_manual",
                        "spending_grant_making_institutions_noncharitable_registered",
                        "spending_grant_making_institutions_noncharitable_360Giving",
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_unknown_manual",
                        "spending_grant_making_institutions_unknown_registered",
                        "spending_grant_making_institutions_unknown_360Giving",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                ),
                then=(
                    Coalesce(
                        "spending_grant_making_individuals_manual",
                        "spending_grant_making_individuals_registered",
                        "spending_grant_making_individuals_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_charitable_manual",
                        "spending_grant_making_institutions_charitable_registered",
                        "spending_grant_making_institutions_charitable_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_noncharitable_manual",
                        "spending_grant_making_institutions_noncharitable_registered",
                        "spending_grant_making_institutions_noncharitable_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_unknown_manual",
                        "spending_grant_making_institutions_unknown_registered",
                        "spending_grant_making_institutions_unknown_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                ),
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
    spending_grant_making_institutions = models.GeneratedField(
        expression=models.Case(
            models.When(
                IsNull(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_manual",
                        "spending_grant_making_institutions_charitable_registered",
                        "spending_grant_making_institutions_charitable_360Giving",
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_noncharitable_manual",
                        "spending_grant_making_institutions_noncharitable_registered",
                        "spending_grant_making_institutions_noncharitable_360Giving",
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_unknown_manual",
                        "spending_grant_making_institutions_unknown_registered",
                        "spending_grant_making_institutions_unknown_360Giving",
                        output_field=models.BigIntegerField(),
                    ),
                    False,
                ),
                then=(
                    Coalesce(
                        "spending_grant_making_institutions_charitable_manual",
                        "spending_grant_making_institutions_charitable_registered",
                        "spending_grant_making_institutions_charitable_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_noncharitable_manual",
                        "spending_grant_making_institutions_noncharitable_registered",
                        "spending_grant_making_institutions_noncharitable_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                    + Coalesce(
                        "spending_grant_making_institutions_unknown_manual",
                        "spending_grant_making_institutions_unknown_registered",
                        "spending_grant_making_institutions_unknown_360Giving",
                        0,
                        output_field=models.BigIntegerField(),
                    )
                ),
            )
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
    notes = MarkdownxField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True, db_index=True)
    date_updated = models.DateTimeField(auto_now=True)

    checked = models.GeneratedField(
        db_persist=True,
        expression=models.Q(
            models.lookups.IsNull(models.F("checked_by"), False),
            models.lookups.IsNull(models.F("notes"), False),
            models.lookups.IsNull(models.F("income_manual"), False),
            models.lookups.IsNull(models.F("spending_manual"), False),
            models.lookups.IsNull(models.F("spending_charitable_manual"), False),
            models.lookups.IsNull(
                models.F("spending_grant_making_individuals_manual"), False
            ),
            models.lookups.IsNull(
                models.F("spending_grant_making_institutions_charitable_manual"), False
            ),
            models.lookups.IsNull(
                models.F("spending_grant_making_institutions_noncharitable_manual"),
                False,
            ),
            models.lookups.IsNull(
                models.F("spending_grant_making_institutions_unknown_manual"), False
            ),
            models.lookups.IsNull(models.F("total_net_assets_manual"), False),
            models.lookups.IsNull(models.F("funds_manual"), False),
            models.lookups.IsNull(models.F("funds_endowment_manual"), False),
            models.lookups.IsNull(models.F("funds_restricted_manual"), False),
            models.lookups.IsNull(models.F("funds_unrestricted_manual"), False),
            models.lookups.IsNull(models.F("employees_manual"), False),
            _connector="OR",
        ),
        output_field=models.BooleanField(),
    )

    class Meta:
        # unique_together = [["financial_year", "financial_year_end"]]
        ordering = ["funder_financial_year", "-financial_year_end"]

    def __str__(self):
        return f"{self.funder_financial_year.funder.name} ({self.financial_year_end})"

    def save(self, *args, **kwargs):
        self.funder_financial_year.save()
        super().save(*args, **kwargs)

    def editable_fields(self) -> list[EditableField]:
        fields = [
            "income",
            "income_investment",
            "spending",
            "spending_investment",
            "spending_grant_making_individuals",
            # "spending_grant_making_institutions",
            # "spending_grant_making_institutions_charitable",
            # "spending_grant_making_institutions_noncharitable",
            "spending_grant_making_institutions_unknown",
            # "total_net_assets",
            # "funds",
            "funds_endowment",
            "funds_restricted",
            "funds_unrestricted",
            "employees",
        ]
        field_labels = {
            "spending_grant_making_institutions_unknown": "Grant making to institutions"
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
