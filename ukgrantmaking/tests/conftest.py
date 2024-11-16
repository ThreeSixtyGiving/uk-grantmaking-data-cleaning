import pytest

from ukgrantmaking.models.cleaningstatus import CleaningStatus, CleaningStatusQuery
from ukgrantmaking.models.financial_years import FinancialYear
from ukgrantmaking.models.funder import Funder


@pytest.fixture
def client_logged_in(admin_user, client):
    client.force_login(admin_user)
    return client


@pytest.fixture
def financial_year():
    fy, _ = FinancialYear.objects.get_or_create(
        fy="2022-23",
        defaults={
            "current": True,
        },
    )
    return fy


@pytest.fixture
def make_funder(financial_year):
    def _make_funder(n=1):
        funder = Funder.objects.create(
            org_id=f"GB-CHC-{n:08}",
            name_registered=f"Test Funder {n}",
        )
        ffy = funder.financial_years.create(
            financial_year=financial_year,
        )
        ffy.financial_years.create(
            financial_year_end=financial_year.grants_end_date,
        )
        funder.save()
        return funder

    return _make_funder


@pytest.fixture
def funder(make_funder):
    return make_funder()


@pytest.fixture
def task():
    return CleaningStatus.objects.create(
        type=CleaningStatus.CleaningStatusType.GRANTMAKER,
        name="Test Task",
    )


@pytest.fixture
def complex_task(make_funder):
    task = CleaningStatus.objects.create(
        type=CleaningStatus.CleaningStatusType.GRANTMAKER,
        name="Test Task",
    )
    # add a condition to the task
    task.cleaningstatusquery_set.create(
        field="financial_year__funder__name",
        comparison=CleaningStatusQuery.Comparison.EQUAL,
        value="Test Funder 1",
    )

    # create two funders - one that matches the condition and one that doesn't
    make_funder(1)
    make_funder(2)

    return task
