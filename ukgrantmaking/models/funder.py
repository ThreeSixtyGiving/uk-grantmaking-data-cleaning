import os

from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.functions import Coalesce, Left, Length, Right, StrIndex
from django.urls import reverse
from django.utils.text import slugify
from markdownx.models import MarkdownxField

from ukgrantmaking.management.commands.funders.fetch_ftc import (
    do_ftc_finance,
    do_ftc_funders,
)
from ukgrantmaking.models.financial_years import FinancialYear, FinancialYearStatus
from ukgrantmaking.models.funder_financial_year import FunderFinancialYear
from ukgrantmaking.models.funder_utils import (
    FUNDER_CATEGORIES,
    FunderSegment,
    RecordStatus,
)
from ukgrantmaking.models.funder_year import FunderYear


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
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey("content_type", "object_id")
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

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]


class Funder(models.Model):
    org_id = models.CharField(max_length=255, primary_key=True)
    charity_number = models.CharField(max_length=255, null=True, blank=True)
    name_registered = models.CharField(max_length=255)
    name_manual = models.CharField(max_length=255, null=True, blank=True)
    segment = models.CharField(
        max_length=50,
        choices=FunderSegment.choices,
        default=FunderSegment.GENERAL_FOUNDATION,
        null=True,
        blank=True,
        db_index=True,
    )
    category = models.GeneratedField(
        expression=models.Case(
            *[
                models.When(segment=segment.value, then=models.Value(category))
                for segment, category in FUNDER_CATEGORIES.items()
            ],
            output_field=models.CharField(max_length=255),
        ),
        output_field=models.CharField(max_length=255),
        db_persist=True,
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
    current_year = models.ForeignKey(
        FunderFinancialYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="funder_current_year",
    )
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
    notes = GenericRelation(FunderNote)

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
        ordering = ["-latest_year__scaling"]

    def __str__(self):
        return f"{self.name} ({self.org_id})"

    @property
    def checked(self):
        if self.current_year:
            if self.current_year.checked_by:
                return self.current_year.checked_by
            if self.current_year.checked:
                return "Checked"
        return False

    def funder_years(self):
        return (
            FunderYear.objects.filter(
                models.Q(
                    new_funder_financial_year__isnull=True,
                    funder_financial_year__funder=self,
                )
                | models.Q(
                    new_funder_financial_year__funder=self,
                    new_funder_financial_year__isnull=False,
                )
            )
            .select_related(
                "funder_financial_year",
                "funder_financial_year__financial_year",
                "funder_financial_year__funder",
                "new_funder_financial_year",
                "new_funder_financial_year__financial_year",
                "new_funder_financial_year__funder",
            )
            .order_by("-financial_year_end")
        )

    def original_funder_years(self):
        return (
            FunderYear.objects.filter(models.Q(funder_financial_year__funder=self))
            .select_related(
                "funder_financial_year",
                "funder_financial_year__financial_year",
                "funder_financial_year__funder",
                "new_funder_financial_year",
                "new_funder_financial_year__financial_year",
                "new_funder_financial_year__funder",
            )
            .order_by("-financial_year_end")
        )

    def log_entries(self):
        return LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
        ).order_by("-action_time")

    def ensure_funder_financial_years(self):
        fys = FinancialYear.objects.filter(
            models.Q(current=True) | ~models.Q(status=FinancialYearStatus.FUTURE)
        ).order_by("-fy")[:5]
        for fy in fys:
            FunderFinancialYear.objects.get_or_create(
                funder=self,
                financial_year=fy,
                defaults={
                    "segment": self.segment,
                    "included": self.included,
                    "makes_grants_to_individuals": self.makes_grants_to_individuals,
                },
            )

    def update_tags(self):
        orgids = {
            "GB-CHC": "ccew",
            "GB-SC": "oscr",
            "GB-NIC": "ccni",
        }
        for prefix, tag in orgids.items():
            if self.org_id.startswith(prefix):
                tag_object, created = FunderTag.objects.get_or_create(
                    slug=tag, defaults={"tag": tag.upper()}
                )
                if not self.tags.filter(tag=tag_object).exists():
                    self.tags.add(tag_object)

    def get_latest_funder_financial_year(self) -> FunderFinancialYear:
        current_fy = FinancialYear.objects.current()
        latest_funder_year = (
            FunderYear.objects.filter(
                funder_financial_year__funder=self,
                funder_financial_year__financial_year=current_fy,
            )
            .order_by("-financial_year_end")
            .first()
        )
        if latest_funder_year:
            return latest_funder_year.funder_financial_year

        new_funder_financial_year, created = FunderFinancialYear.objects.get_or_create(
            funder=self, financial_year=current_fy
        )
        return new_funder_financial_year

    def update_funder_financial_year(self):
        self.current_year = self.get_latest_funder_financial_year()
        self.current_year.update_fields()
        self.current_year.save()

        current_fy = FinancialYear.objects.current()
        if current_fy.status == FinancialYearStatus.OPEN:
            self.current_year.segment = self.segment
            self.current_year.included = self.included
            self.current_year.makes_grants_to_individuals = (
                self.makes_grants_to_individuals
            )
            self.current_year.save()
            self.current_year.tags.set(self.tags.all())

    def transfer_funder_financial_years_to_successor(self):
        # transfer financial years to successor
        if self.successor:
            for funder_financial_year in self.funder_financial_years.all():
                for funder_year in funder_financial_year.funder_years.all():
                    funder_year.new_funder_financial_year, created = (
                        FunderFinancialYear.objects.get_or_create(
                            funder=self.successor,
                            financial_year=funder_financial_year.financial_year,
                            defaults={
                                "segment": funder_financial_year.segment,
                                "included": funder_financial_year.included,
                                "makes_grants_to_individuals": funder_financial_year.makes_grants_to_individuals,
                            },
                        )
                    )
                    funder_year.save()

    def get_absolute_url(self):
        return reverse("grantmakers:detail", kwargs={"org_id": self.pk})

    def update_from_ftc(self):
        do_ftc_funders(
            db_con=os.environ.get("FTC_DB_URL"),
            org_ids=(self.org_id,),
            debug=True,
        )
        do_ftc_finance(
            db_con=os.environ.get("FTC_DB_URL"),
            org_ids=(self.org_id,),
            debug=True,
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # make sure the funder has last five funder financial years
        self.ensure_funder_financial_years()

        # update auto-generated tags
        self.update_tags()

        # update the funder financial year with the latest values
        self.update_funder_financial_year()

        # transfer financial years to successor
        self.transfer_funder_financial_years_to_successor()

        # transfer financial years from predecessors
        if self.predecessors.exists():
            for predecessor in self.predecessors.all():
                predecessor.save()
