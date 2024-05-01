from django.db import models


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
    regrant_type = models.CharField(max_length=255, null=True, blank=True)
    location_scope = models.CharField(max_length=255, null=True, blank=True)
    grant_programme_title = models.CharField(max_length=255, null=True, blank=True)
    publisher_prefix = models.CharField(max_length=255, null=True, blank=True)
    publisher_name = models.CharField(max_length=255, null=True, blank=True)
    license = models.CharField(max_length=255, null=True, blank=True)

    funder = models.ForeignKey(
        "Funder", on_delete=models.CASCADE, related_name="grants", null=True, blank=True
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

    def __str__(self):
        return "Grant from {} to {} for {}{:,.0f} ({})".format(
            self.funding_organisation_name,
            self.recipient_organisation_name,
            self.currency if self.currency != "GBP" else "£",
            self.amount_awarded,
            self.award_date.year,
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
