from django.db import models
from django.db.models.functions import Coalesce, Left, Length, Right, StrIndex

from ukgrantmaking.models.financial_years import FinancialYears


class Grant(models.Model):
    class RecipientType(models.TextChoices):
        ORGANISATION = "Organisation", "Organisation"
        INDIVIDUAL = "Individual", "Individual"
        CHARITY = "Charity", "Charity"
        COMMUNITY_INTEREST_COMPANY = (
            "Community Interest Company",
            "Community Interest Company",
        )
        EDUCATION = "Education", "Education"
        GOVERNMENT_DEPARTMENT = "Government Department", "Government Department"
        LOCAL_AUTHORITY = "Local Authority", "Local Authority"
        MUTUAL = "Mutual", "Mutual"
        NDPB = "NDPB", "NDPB"
        NHS = "NHS", "NHS"
        NON_PROFIT_COMPANY = "Non-profit Company", "Non-profit Company"
        OVERSEAS_CHARITY = "Overseas Charity", "Overseas Charity"
        OVERSEAS_GOVERNMENT = "Overseas Government", "Overseas Government"
        PRIVATE_COMPANY = "Private Company", "Private Company"
        UNIVERSITY = "University", "University"
        RELIGIOUS_ORGANISATION = "Religious Organisation", "Religious Organisation"
        SPORTS_CLUB = "Sports Club", "Sports Club"

    class FunderType(models.TextChoices):
        GRANTMAKING_ORGANISATION = (
            "Grantmaking Organisation",
            "Grantmaking Organisation",
        )
        LOTTERY_DISTRIBUTOR = "Lottery Distributor", "Lottery Distributor"
        CENTRAL_GOVERNMENT = "Central Government", "Central Government"
        LOCAL_GOVERNMENT = "Local Government", "Local Government"
        DEVOLVED_GOVERNMENT = "Devolved Government", "Devolved Government"

    class InclusionStatus(models.TextChoices):
        INCLUDED = "Included", "Included"
        UNSURE = "Unsure", "Unsure"
        DUPLICATE_GRANT = "Duplicate grant", "Duplicate grant"
        GOVERNMENT_TRANSFER = "Government transfer", "Government transfer"
        LOCAL_AUTHORITY_GRANT = "Local Authority Grant", "Local Authority Grant"
        OVERSEAS_GOVERNMENT_TRANSFER = (
            "Overseas government transfer",
            "Overseas government transfer",
        )
        PRIVATE_SECTOR_GRANT = "Private sector grant", "Private sector grant"
        GRANT_TO_EDUCATION = "Grant to education", "Grant to education"

    class RegrantType(models.TextChoices):
        FRG010 = (
            "FRG010",
            "Common Regrant",
        )  # A grant awarded to a single grantmaking organisation for onward distribution as grants to end recipients.
        FRG020 = (
            "FRG020",
            "Transfer to intermediary",
        )  # A grant awarded to an intermediary, such as a network or federated charity, for distribution as payment to organisation(s) for redistribution as grants to end recipients.
        FRG030 = (
            "FRG030",
            "Match funding",
        )  # A grant awarded to grantmaking organisations for match funding and onwards distribution as grants to end recipients.
        FRG040 = (
            "FRG040",
            "Funder collaboration",
        )  # Grants awarded by multiple funders to a single grantmaking organisation to create a fund for redistribution as grants to end recipients.
        FRG050 = (
            "FRG050",
            "Fiscal sponsor",
        )  # Grant awarded to an organisation acting as an agent for the funder, to make grant payments on its behalf to the defined recipient(s).
        FRG060 = (
            "FRG060",
            "Endowment",
        )  # A single grant awarded or transfer of capital to either establish or substantially fund a grantmaking organisation or Fund.
        FRG070 = (
            "FRG070",
            "Multipurpose",
        )  # Grant to recipient for activities that include making onward grants, as well as funding other activities not related to the distribution of grants.

    class LocationScope(models.TextChoices):
        GLS010 = "GLS010", "Global"  # The location scope is global.
        GLS020 = (
            "GLS020",
            "Supranational",
        )  # The location scope is a supranational region or continent.
        GLS030 = (
            "GLS030",
            "National",
        )  # The activity scope covers a country, as defined by ISO 3166.
        GLS040 = (
            "GLS040",
            "Subnational region",
        )  # The activity scope covers a first-level subnational administrative area.
        GLS050 = (
            "GLS050",
            "Local authority",
        )  # The activity scope covers a second-level subnational administrative area.
        GLS060 = "GLS060", "Local area"  # Location scope covers a small area.
        GLS099 = "GLS099", "Undefined"  # The location scope is undefined.

    grant_id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="GBP")
    amount_awarded = models.DecimalField(max_digits=16, decimal_places=2, db_index=True)
    amount_awarded_GBP = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, db_index=True
    )
    award_date = models.DateField()
    planned_dates_duration = models.FloatField(null=True, blank=True)
    planned_dates_startDate = models.DateField(null=True, blank=True)
    planned_dates_endDate = models.DateField(null=True, blank=True)
    recipient_organisation_id = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    recipient_organisation_name = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    recipient_individual_id = models.CharField(max_length=255, null=True, blank=True)
    recipient_individual_name = models.CharField(max_length=255, null=True, blank=True)
    recipient_individual_primary_grant_reason = models.CharField(
        max_length=255, null=True, blank=True
    )
    recipient_individual_secondary_grant_reason = models.CharField(
        max_length=255, null=True, blank=True
    )
    recipient_individual_grant_purpose = models.CharField(
        max_length=255, null=True, blank=True
    )
    recipient_type = models.CharField(
        max_length=50,
        choices=RecipientType.choices,
        default=RecipientType.ORGANISATION,
        db_index=True,
    )
    funding_organisation_id = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    funding_organisation_name = models.CharField(
        max_length=255, null=True, blank=True, db_index=True
    )
    funding_organisation_type = models.CharField(
        max_length=50,
        choices=FunderType.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    regrant_type_registered = models.CharField(
        max_length=255, null=True, blank=True, choices=RegrantType.choices
    )
    regrant_type_manual = models.CharField(
        max_length=255, null=True, blank=True, choices=RegrantType.choices
    )
    regrant_type = models.GeneratedField(
        expression=Coalesce("regrant_type_manual", "regrant_type_registered"),
        output_field=models.CharField(max_length=255, null=True, blank=True),
        db_persist=True,
    )
    location_scope = models.CharField(
        max_length=255, null=True, blank=True, choices=LocationScope.choices
    )
    grant_programme_title = models.CharField(max_length=255, null=True, blank=True)
    publisher_prefix = models.CharField(max_length=255, null=True, blank=True)
    publisher_name = models.CharField(max_length=255, null=True, blank=True)
    license = models.CharField(max_length=255, null=True, blank=True)

    funder = models.ForeignKey(
        "Funder", on_delete=models.CASCADE, related_name="grants", null=True, blank=True
    )
    recipient = models.ForeignKey(
        "GrantRecipient",
        on_delete=models.CASCADE,
        related_name="grants",
        null=True,
        blank=True,
    )
    recipient_type_manual = models.CharField(
        max_length=50,
        choices=RecipientType.choices,
        default=None,
        null=True,
        blank=True,
        db_index=True,
    )
    inclusion = models.CharField(
        max_length=50,
        choices=InclusionStatus.choices,
        default=InclusionStatus.UNSURE,
        db_index=True,
        verbose_name="Exclusion status",
    )
    notes = models.TextField(null=True, blank=True)
    checked_by = models.CharField(max_length=255, null=True, blank=True)

    annual_amount = models.GeneratedField(
        expression=models.Case(
            models.When(
                planned_dates_duration__isnull=False,
                then=(
                    models.functions.Cast(
                        models.F("amount_awarded_GBP"), models.FloatField()
                    )
                    / models.F("planned_dates_duration")
                )
                * models.Value(12),
            ),
            default=models.functions.Cast(
                models.F("amount_awarded_GBP"), models.FloatField()
            ),
        ),
        output_field=models.DecimalField(max_digits=16, decimal_places=2),
        db_persist=True,
    )

    def __str__(self):
        return "Grant from {} to {} for {}{:,.0f} ({})".format(
            self.funding_organisation_name or "",
            self.recipient_organisation_name or "",
            self.currency if self.currency != "GBP" else "£",
            self.amount_awarded or 0,
            self.award_date.year if self.award_date else "unknown",
        )


class CurrencyConverter(models.Model):
    currency = models.CharField(max_length=3)
    date = models.DateField()
    rate = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.currency

    class Meta:
        unique_together = [["currency", "date"]]
        ordering = ["currency", "-date"]


class GrantRecipient(models.Model):
    class RecipientScale(models.TextChoices):
        LOCAL = "Local", "Local"
        NATIONAL = "National", "National"
        OVERSEAS = "Overseas", "Overseas"
        NATIONAL_OVERSEAS = "National and Overseas", "National and Overseas"

    recipient_id = models.CharField(max_length=255, primary_key=True)
    name_registered = models.CharField(max_length=255)
    name_manual = models.CharField(max_length=255, null=True, blank=True)
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

    type = models.CharField(max_length=50, choices=Grant.RecipientType.choices)
    date_of_registration = models.DateField(null=True, blank=True)
    date_of_removal = models.DateField(null=True, blank=True)
    active = models.BooleanField(null=True, blank=True)

    scale_registered = models.CharField(
        max_length=50, null=True, blank=True, choices=RecipientScale.choices
    )
    scale_manual = models.CharField(
        max_length=50, null=True, blank=True, choices=RecipientScale.choices
    )
    scale = models.GeneratedField(
        expression=Coalesce("scale_manual", "scale_registered"),
        output_field=models.CharField(
            max_length=50, null=True, blank=True, choices=RecipientScale.choices
        ),
        db_persist=True,
    )

    org_id_schema = models.GeneratedField(
        expression=models.Case(
            models.When(
                models.Q(recipient_id__startswith="UKG-"),
                then=models.Value("UKG"),
            ),
            models.When(
                models.Q(recipient_id__startswith="360G-"),
                then=models.Value("UKG"),
            ),
            models.When(
                models.Q(recipient_id__startswith="GB-CHC-"),
                then=models.Value("GB-CHC"),
            ),
            models.When(
                models.Q(recipient_id__startswith="GB-COH-"),
                then=models.Value("GB-COH"),
            ),
            models.When(
                models.Q(recipient_id__startswith="GB-SC-"),
                then=models.Value("GB-SC"),
            ),
            models.When(
                models.Q(recipient_id__startswith="GB-NIC-"),
                then=models.Value("GB-NIC"),
            ),
            models.When(
                models.Q(recipient_id__startswith="GB-LAE-"),
                then=models.Value("GB-LAE"),
            ),
            models.When(
                models.Q(recipient_id__startswith="GB-GOR-"),
                then=models.Value("GB-GOR"),
            ),
            models.When(
                models.Q(("recipient_id__startswith", "GB-SHPE-")),
                then=models.Value("GB-SHPE"),
            ),
            models.When(
                models.Q(("recipient_id__startswith", "GB-NHS-")),
                then=models.Value("GB-NHS"),
            ),
            models.When(
                models.Q(("recipient_id__startswith", "GB-LAS-")),
                then=models.Value("GB-LAS"),
            ),
            models.When(
                models.Q(("recipient_id__startswith", "GB-PLA-")),
                then=models.Value("GB-PLA"),
            ),
            models.When(
                models.Q(("recipient_id__startswith", "GB-LANI-")),
                then=models.Value("GB-LANI"),
            ),
            models.When(
                models.Q(("recipient_id__startswith", "US-EIN-")),
                then=models.Value("US-EIN"),
            ),
            models.When(
                models.Q(("recipient_id__startswith", "XI-ROR-")),
                then=models.Value("XI-ROR"),
            ),
            models.When(
                models.Q(("recipient_id__startswith", "XI-PB-")),
                then=models.Value("XI-PB"),
            ),
            default=Left(
                models.F("recipient_id"),
                StrIndex(models.F("recipient_id"), models.Value("-")) - 1,
            ),
        ),
        output_field=models.CharField(max_length=255),
        db_persist=True,
    )

    def __str__(self):
        return self.name


class GrantRecipientYear(models.Model):
    recipient = models.ForeignKey("GrantRecipient", on_delete=models.CASCADE)
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

    employees_registered = models.IntegerField(null=True, blank=True)
    employees_manual = models.IntegerField(null=True, blank=True)
    employees = models.GeneratedField(
        expression=Coalesce("employees_manual", "employees_registered"),
        output_field=models.BigIntegerField(),
        db_persist=True,
    )
