from typing import Callable

import pytest
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, QuerySet
from django.test import Client

from ukgrantmaking.models.cleaningstatus import (
    CleaningStatus,
    CleaningStatusType,
    Comparison,
)
from ukgrantmaking.models.financial_years import FinancialYear, FinancialYearStatus
from ukgrantmaking.models.funder import Funder, FunderTag


@pytest.fixture
def client_logged_in(admin_user: AbstractBaseUser, client: Client) -> Client:
    client.force_login(admin_user)
    return client


@pytest.fixture
def financial_year() -> FinancialYear:
    fy, _ = FinancialYear.objects.update_or_create(
        fy="2022-23",
        defaults={
            "current": True,
            "status": FinancialYearStatus.OPEN,
        },
    )
    return fy


@pytest.fixture
def tag() -> FunderTag:
    tag, _ = FunderTag.objects.get_or_create(
        slug="example-tag",
        defaults={
            "tag": "Example Tag",
        },
    )
    return tag


@pytest.fixture
def make_funder(
    financial_year: FinancialYear, tag: FunderTag
) -> Callable[[int], Funder]:
    def _make_funder(n: int = 1) -> Funder:
        funder = Funder.objects.create(
            org_id=f"GB-CHC-{n:08}",
            name_registered=f"Test Funder {n}",
        )
        funder_financial_year, _ = funder.funder_financial_years.get_or_create(
            financial_year=financial_year,
        )
        funder_financial_year.funder_years.get_or_create(
            financial_year_end=financial_year.grants_end_date,
        )
        funder.save()

        funder.tags.set([tag])
        return funder

    return _make_funder


@pytest.fixture
def funder(make_funder: Callable[[int], Funder]) -> Funder:
    return make_funder()


@pytest.fixture
def funder_with_py(make_funder: Callable[[int], Funder]) -> Funder:
    funder = make_funder(2)

    fy, _ = FinancialYear.objects.update_or_create(
        fy="2021-22",
        defaults={
            "current": False,
            "status": FinancialYearStatus.CLOSED,
        },
    )
    funder_financial_year, _ = funder.funder_financial_years.get_or_create(
        financial_year=fy,
    )
    funder_financial_year.funder_years.create(
        financial_year_end=fy.grants_end_date,
    )
    funder.save()

    return funder


@pytest.fixture
def task() -> CleaningStatus:
    return CleaningStatus.objects.create(
        type=CleaningStatusType.GRANTMAKER,
        name="Test Task",
    )


@pytest.fixture
def complex_task(make_funder: Callable[[int], Funder]) -> CleaningStatus:
    task = CleaningStatus.objects.create(
        type=CleaningStatusType.GRANTMAKER,
        name="Test Task",
    )
    # add a condition to the task
    task.cleaningstatusquery_set.create(
        field="funder__name",
        comparison=Comparison.EQUAL,
        value="Test Funder 1",
    )

    # create two funders - one that matches the condition and one that doesn't
    make_funder(1)
    make_funder(2)

    return task


@pytest.fixture
def check_log_entry(
    admin_user: AbstractBaseUser,
) -> Callable[[object, str], QuerySet[LogEntry] | None]:
    def _check_log_entry(
        obj: Model, action: str = "Changed"
    ) -> QuerySet[LogEntry] | None:
        action = {
            "added": ADDITION,
            "changed": CHANGE,
            "deleted": DELETION,
        }.get(action.lower(), action)
        assert action in [ADDITION, CHANGE, DELETION]
        results = LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            action_flag=action,
            user=admin_user,
            object_id=obj.pk,
        ).all()
        if results:
            return results
        return None

    return _check_log_entry
