from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.functions import Coalesce, Left, Length, Right, StrIndex
from django.utils.text import slugify
from markdownx.models import MarkdownxField

from ukgrantmaking.models.financial_years import FinancialYear
from ukgrantmaking.models.funder_utils import FunderSegment, RecordStatus
from ukgrantmaking.models.funder_year import FunderFinancialYear, FunderYear


class FunderTag(models.Model):
    slug = models.SlugField(max_length=255, primary_key=True)
    tag = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    def __str__(self):
        if self.parent:
            return f"{self.parent} - {self.tag}"
        return self.tag

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.tag)
        super().save(*args, **kwargs)


class FunderNote(models.Model):
    funder = models.ForeignKey("Funder", on_delete=models.CASCADE, related_name="notes")
    note = MarkdownxField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="funder_notes_added",
    )
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

    successor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="predecessors",
    )

    status = models.CharField(
        max_length=50,
        choices=RecordStatus.choices,
        default=RecordStatus.UNCHECKED,
        db_index=True,
    )

    date_of_registration = models.DateField(null=True, blank=True)
    date_of_removal = models.DateField(null=True, blank=True)
    active = models.BooleanField(null=True, blank=True)
    activities = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    latest_year = models.ForeignKey(
        FunderFinancialYear,
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
        ordering = ["-latest_year__spending_grant_making"]

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

    def log_entries(self):
        return LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
        ).order_by("-action_time")

    def save(self, *args, **kwargs):
        current_fy = FinancialYear.objects.current()
        latest_fy = (
            FunderYear.objects.filter(
                financial_year__funder=self, financial_year__financial_year=current_fy
            )
            .order_by("-financial_year_end")
            .first()
        )
        if latest_fy:
            self.latest_year = latest_fy.financial_year

            if (
                latest_fy.spending_grant_making_individuals
                and latest_fy.spending_grant_making_individuals > 0
            ):
                self.makes_grants_to_individuals = True
        else:
            self.latest_year = FunderFinancialYear.objects.filter(
                funder=self, financial_year=current_fy
            ).first()
            if not self.latest_year:
                self.latest_year = FunderFinancialYear.objects.create(
                    funder=self, financial_year=current_fy
                )

        # # transfer financial years to successor
        # @TODO work out the logic for this
        # if self.successor:
        #     for fy in FunderYear.objects.filter(financial_year__funder=self):
        #         fy.funder = self.successor
        #         fy.save()

        # # transfer financial years from predecessors
        # if self.predecessors.exists():
        #     for predecessor in self.predecessors.all():
        #         for fy in predecessor.funderyear_set.all():
        #             fy.funder = self
        #             fy.save()

        super().save(*args, **kwargs)
        if self.latest_year:
            self.latest_year.save()
