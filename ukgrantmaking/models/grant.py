from django.db import models


class Grant(models.Model):
    class RecipientType(models.TextChoices):
        ORGANISATION = "Organisation", "Organisation"
        INDIVIDUAL = "Individual", "Individual"

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
    inclusion = models.CharField(
        max_length=50,
        choices=InclusionStatus.choices,
        default=InclusionStatus.UNSURE,
        db_index=True,
    )
    notes = models.TextField(null=True, blank=True)
    checked_by = models.CharField(max_length=255, null=True, blank=True)


class CurrencyConverter(models.Model):
    currency = models.CharField(max_length=3)
    date = models.DateField()
    rate = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.currency

    class Meta:
        unique_together = [["currency", "date"]]
        ordering = ["currency", "-date"]
