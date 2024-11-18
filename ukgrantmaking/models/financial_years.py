from django.db import models


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
DEFAULT_BREAK_MONTH = 5


class FinancialYearManager(models.Manager):
    def current(self):
        return self.get_queryset().get(current=True)


class FinancialYearStatus(models.TextChoices):
    OPEN = "Open", "Open"
    CLOSED = "Closed", "Closed"
    FUTURE = "Future", "Future"


class FinancialYear(models.Model):
    fy = models.CharField(
        max_length=7,
        choices=FinancialYears.choices,
        default=DEFAULT_FINANCIAL_YEAR,
        primary_key=True,
    )
    funders_start_date = models.DateField()
    funders_end_date = models.DateField()
    grants_start_date = models.DateField()
    grants_end_date = models.DateField()

    current = models.BooleanField(default=False)

    status = models.CharField(
        max_length=6,
        choices=FinancialYearStatus.choices,
        default=FinancialYearStatus.CLOSED,
    )

    objects = FinancialYearManager()

    @property
    def first_year(self):
        years = self.fy.split("-")
        return int(years[0])

    @property
    def last_year(self):
        return self.first_year + 1

    def __str__(self):
        return f"FY {self.fy}"

    def save(self, *args, **kwargs):
        if not self.funders_start_date:
            self.funders_start_date = f"{self.first_year}-05-01"
        if not self.funders_end_date:
            self.funders_end_date = f"{self.last_year}-04-30"
        if not self.grants_start_date:
            self.grants_start_date = f"{self.first_year}-04-01"
        if not self.grants_end_date:
            self.grants_end_date = f"{self.last_year}-03-31"

        if self.current:
            FinancialYear.objects.filter(current=True).exclude(fy=self.fy).update(
                current=False
            )
        super().save(*args, **kwargs)
