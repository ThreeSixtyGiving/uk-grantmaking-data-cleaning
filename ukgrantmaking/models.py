from django.db import models
from django.db.models.functions import Coalesce, Left, Length, Right, StrIndex
from django.db.models.lookups import IsNull


class FinancialYears(models.TextChoices):
    FY_2029_30 = "2029-30", "2029-30"
    FY_2028_29 = "2028-29", "2028-29"
    FY_2027_28 = "2027-28", "2027-28"
    FY_2026_27 = "2026-27", "2026-27"
    FY_2025_26 = "2025-26", "2025-26"
    FY_2024_25 = "2024-25", "2024-25"
    FY_2023_24 = "2023-24", "2023-24"
    FY_2022_23 = "2022-23", "2022-23"
    FY_2021_22 = "2021-22", "2021-22"
    FY_2020_21 = "2020-21", "2020-21"
    FY_2019_20 = "2019-20", "2019-20"
    FY_2018_19 = "2018-19", "2018-19"
    FY_2017_18 = "2017-18", "2017-18"
    FY_2016_17 = "2016-17", "2016-17"
    FY_2015_16 = "2015-16", "2015-16"
    FY_2014_15 = "2014-15", "2014-15"
    FY_2013_14 = "2013-14", "2013-14"
    FY_2012_13 = "2012-13", "2012-13"
    FY_2011_12 = "2011-12", "2011-12"
    FY_2010_11 = "2010-11", "2010-11"
    FY_2009_10 = "2009-10", "2009-10"
    FY_2008_09 = "2008-09", "2008-09"
    FY_2007_08 = "2007-08", "2007-08"
    FY_2006_07 = "2006-07", "2006-07"
    FY_2005_06 = "2005-06", "2005-06"
    FY_2004_05 = "2004-05", "2004-05"
    FY_2003_04 = "2003-04", "2003-04"
    FY_2002_03 = "2002-03", "2002-03"
    FY_2001_02 = "2001-02", "2001-02"
    FY_2000_01 = "2000-01", "2000-01"


DEFAULT_FINANCIAL_YEAR = FinancialYears.FY_2022_23


class FunderSegment(models.TextChoices):
    DONOR_ADVISED_FUND = "Donor Advised Fund", "Donor Advised Fund"
    WELLCOME_TRUST = "Wellcome Trust", "Wellcome Trust"
    CHARITY = "Charity", "Charity"
    LOTTERY_DISTRIBUTOR = "Lottery Distributor", "Lottery Distributor"
    ARMS_LENGTH_BODY = "Arms Length Body", "Arms Length Body"
    CORPORATE_FOUNDATION = "Corporate Foundation", "Corporate Foundation"
    FAMILY_FOUNDATION = "Family Foundation", "Family Foundation"
    FUNDRAISING_GRANTMAKER = "Fundraising Grantmaker", "Fundraising Grantmaker"
    GENERAL_GRANTMAKER = "General grantmaker", "General grantmaker"
    MEMBER_TRADE_FUNDED = "Member/Trade Funded", "Member/Trade Funded"
    NHS_HOSPITAL_FOUNDATION = "NHS/Hospital Foundation", "NHS/Hospital Foundation"
    GOVERNMENT_LOTTERY_ENDOWED = (
        "Government/Lottery Endowed",
        "Government/Lottery Endowed",
    )
    SMALL_GRANTMAKER = "Small grantmaker", "Small grantmaker"
    COMMUNITY_FOUNDATION = "Community Foundation", "Community Foundation"
    LOCAL = "Local", "Local"
    CENTRAL = "Central", "Central"
    DEVOLVED = "Devolved", "Devolved"

    def category(self):
        return FUNDER_CATEGORIES[self]


class FunderCategory(models.TextChoices):
    GRANTMAKER = "Grantmaker", "Grantmaker"
    LOTTERY = "Lottery", "Lottery"
    CHARITY = "Charity", "Charity"
    GOVERNMENT = "Government", "Government"
    OTHER = "Other", "Other"


FUNDER_CATEGORIES = {
    FunderSegment.COMMUNITY_FOUNDATION: FunderCategory.GRANTMAKER,
    FunderSegment.CORPORATE_FOUNDATION: FunderCategory.GRANTMAKER,
    FunderSegment.FAMILY_FOUNDATION: FunderCategory.GRANTMAKER,
    FunderSegment.FUNDRAISING_GRANTMAKER: FunderCategory.GRANTMAKER,
    FunderSegment.GENERAL_GRANTMAKER: FunderCategory.GRANTMAKER,
    FunderSegment.GOVERNMENT_LOTTERY_ENDOWED: FunderCategory.GRANTMAKER,
    FunderSegment.MEMBER_TRADE_FUNDED: FunderCategory.GRANTMAKER,
    FunderSegment.SMALL_GRANTMAKER: FunderCategory.GRANTMAKER,
    FunderSegment.WELLCOME_TRUST: FunderCategory.GRANTMAKER,
    FunderSegment.LOTTERY_DISTRIBUTOR: FunderCategory.LOTTERY,
    FunderSegment.CHARITY: FunderCategory.CHARITY,
    FunderSegment.NHS_HOSPITAL_FOUNDATION: FunderCategory.CHARITY,
    FunderSegment.LOCAL: FunderCategory.GOVERNMENT,
    FunderSegment.CENTRAL: FunderCategory.GOVERNMENT,
    FunderSegment.DEVOLVED: FunderCategory.GOVERNMENT,
    FunderSegment.ARMS_LENGTH_BODY: FunderCategory.GOVERNMENT,
    FunderSegment.DONOR_ADVISED_FUND: FunderCategory.OTHER,
}


class FunderTag(models.Model):
    tag = models.CharField(max_length=255, primary_key=True)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    def __str__(self):
        return self.tag


class FunderNote(models.Model):
    funder = models.ForeignKey("Funder", on_delete=models.CASCADE, related_name="notes")
    note = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    added_by = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.note


class Funder(models.Model):
    org_id = models.CharField(max_length=255, primary_key=True)
    charity_number = models.CharField(max_length=255, null=True, blank=True)
    name_registered = models.CharField(max_length=255)
    name_manual = models.CharField(max_length=255, null=True, blank=True)
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
    date_of_registration = models.DateField(null=True, blank=True)
    activities = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    latest_grantmaking = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True, db_index=True
    )
    latest_year = models.ForeignKey(
        "FunderYear",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="funder_latest_year",
    )

    org_id_schema = models.GeneratedField(
        expression=models.Case(
            models.When(
                models.Q(org_id__startswith="UKG-"),
                then=models.Value("UKG"),
            ),
            models.When(
                models.Q(org_id__startswith="360G-"),
                then=models.Value("UKG"),
            ),
            models.When(
                models.Q(org_id__startswith="GB-CHC-"),
                then=models.Value("GB-CHC"),
            ),
            models.When(
                models.Q(org_id__startswith="GB-COH-"),
                then=models.Value("GB-COH"),
            ),
            models.When(
                models.Q(org_id__startswith="GB-SC-"),
                then=models.Value("GB-SC"),
            ),
            models.When(
                models.Q(org_id__startswith="GB-NIC-"),
                then=models.Value("GB-NIC"),
            ),
            models.When(
                models.Q(org_id__startswith="GB-LAE-"),
                then=models.Value("GB-LAE"),
            ),
            models.When(
                models.Q(org_id__startswith="GB-GOR-"),
                then=models.Value("GB-GOR"),
            ),
            models.When(
                models.Q(("org_id__startswith", "GB-SHPE-")),
                then=models.Value("GB-SHPE"),
            ),
            models.When(
                models.Q(("org_id__startswith", "GB-NHS-")),
                then=models.Value("GB-NHS"),
            ),
            models.When(
                models.Q(("org_id__startswith", "GB-LAS-")),
                then=models.Value("GB-LAS"),
            ),
            models.When(
                models.Q(("org_id__startswith", "GB-PLA-")),
                then=models.Value("GB-PLA"),
            ),
            models.When(
                models.Q(("org_id__startswith", "GB-LANI-")),
                then=models.Value("GB-LANI"),
            ),
            models.When(
                models.Q(("org_id__startswith", "US-EIN-")),
                then=models.Value("US-EIN"),
            ),
            models.When(
                models.Q(("org_id__startswith", "XI-ROR-")),
                then=models.Value("XI-ROR"),
            ),
            models.When(
                models.Q(("org_id__startswith", "XI-PB-")),
                then=models.Value("XI-PB"),
            ),
            default=Left(
                models.F("org_id"), StrIndex(models.F("org_id"), models.Value("-")) - 1
            ),
        ),
        output_field=models.CharField(max_length=255),
        db_persist=True,
    )

    tags = models.ManyToManyField(FunderTag, blank=True, related_name="funders")

    name = models.GeneratedField(
        expression=Coalesce(
            "name_manual",
            models.Case(
                models.When(
                    name_registered__startswith="The ",
                    then=Right(
                        models.F("name_registered"),
                        Length(models.F("name_registered")) - 4,
                    ),
                ),
                default=models.F("name_registered"),
            ),
        ),
        output_field=models.CharField(max_length=255),
        db_persist=True,
    )

    class Meta:
        ordering = ["-latest_grantmaking"]

    def __str__(self):
        return f"{self.name} ({self.org_id})"

    def save(self, *args, **kwargs):
        latest_fy = (
            self.funderyear_set.filter(financial_year=DEFAULT_FINANCIAL_YEAR)
            .order_by("-financial_year_end")
            .first()
        )
        if latest_fy:
            self.latest_year = latest_fy
            if latest_fy.spending_grant_making is not None:
                self.latest_grantmaking = latest_fy.spending_grant_making
            elif latest_fy.spending_grant_making_institutions:
                self.latest_grantmaking = latest_fy.spending_grant_making_institutions
            elif latest_fy.spending_charitable:
                self.latest_grantmaking = latest_fy.spending_charitable
            elif latest_fy.spending:
                self.latest_grantmaking = latest_fy.spending
            else:
                self.latest_grantmaking = None

            if (
                latest_fy.spending_grant_making_individuals
                and latest_fy.spending_grant_making_individuals > 0
            ):
                self.makes_grants_to_individuals = True
        else:
            self.latest_year = None
            self.latest_grantmaking = None

        super().save(*args, **kwargs)


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

    checked_on = models.DateTimeField(auto_now=True)
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
