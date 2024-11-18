# test whether the admin pages for all the models in the ukgrantmaking app are working
import pytest
from django.urls import reverse


@pytest.mark.parametrize(
    "model",
    [
        "cleaningstatus",
        "funder",
        "fundertag",
        "funderfinancialyear",
        "funderyear",
        "financialyear",
    ],
)
def test_admin_list_pages(client_logged_in, funder_with_py, model):
    url = reverse(f"admin:ukgrantmaking_{model}_changelist")
    response = client_logged_in.get(url)
    assert response.status_code == 200


def test_admin_funder_page(client_logged_in, funder_with_py):
    funder = funder_with_py

    url = reverse("admin:ukgrantmaking_funder_change", args=[funder.pk])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert funder.name_registered in response.content.decode()


def test_admin_funder_year_page(client_logged_in, funder_with_py):
    funder = funder_with_py
    fy = funder.latest_year.funder_years.first()
    url = reverse("admin:ukgrantmaking_funderyear_change", args=[fy.pk])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert fy.financial_year_end.strftime("%Y-%m-%d") in response.content.decode()


def test_admin_funder_financial_year_page(client_logged_in, funder_with_py):
    funder = funder_with_py
    fy = funder.latest_year
    url = reverse("admin:ukgrantmaking_funderfinancialyear_change", args=[fy.pk])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert fy.financial_year.fy in response.content.decode()


def test_admin_financial_year_page(client_logged_in, funder_with_py):
    funder = funder_with_py
    fy = funder.latest_year.financial_year
    url = reverse("admin:ukgrantmaking_financialyear_change", args=[fy.pk])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert fy.fy in response.content.decode()


def test_admin_funder_tag_page(client_logged_in, tag):
    url = reverse("admin:ukgrantmaking_fundertag_change", args=[tag.pk])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert tag.tag in response.content.decode()


def test_admin_cleaningstatus_page(client_logged_in, complex_task):
    url = reverse("admin:ukgrantmaking_cleaningstatus_change", args=[complex_task.pk])
    response = client_logged_in.get(url)
    assert response.status_code == 200
    assert complex_task.name in response.content.decode()
