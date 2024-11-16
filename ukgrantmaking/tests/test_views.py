import pytest


@pytest.mark.parametrize(
    "url", ["/", "/table-creator/", "/export/funders.xlsx", "/export/grants.xlsx"]
)
def test_not_logged_in(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"


def test_index(client_logged_in):
    response = client_logged_in.get("/")
    assert response.status_code == 200
    assert "Number of grantmakers" in response.content.decode("utf-8")


def test_table_creator(client_logged_in):
    response = client_logged_in.get("/table-creator/")
    assert response.status_code == 200


def test_funder_export(client_logged_in):
    response = client_logged_in.get("/export/funders.xlsx")
    assert response.status_code == 200


def test_grants_export(client_logged_in):
    response = client_logged_in.get("/export/grants.xlsx")
    assert response.status_code == 200
