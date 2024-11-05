from django.db import models
from django.db.models.functions import Coalesce, Left, Length, Right, StrIndex
from markdownx.models import MarkdownxField

from ukgrantmaking.models.financial_years import DEFAULT_FINANCIAL_YEAR


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

    @property
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
    note = MarkdownxField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    added_by = models.CharField(max_length=255, null=True, blank=True)
    resolved = models.BooleanField(default=False)

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
    date_of_removal = models.DateField(null=True, blank=True)
    active = models.BooleanField(null=True, blank=True)
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

    @property
    def checked(self):
        if self.latest_year:
            if self.latest_year.checked_by:
                return self.latest_year.checked_by
            if self.latest_year.checked:
                return "Checked"
        return False

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
