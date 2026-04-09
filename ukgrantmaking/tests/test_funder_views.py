import pytest
from django.test import Client

from ukgrantmaking.models.cleaningstatus import CleaningStatus
from ukgrantmaking.models.funder import Funder

# urls:
GRANTMAKER_URLS = [
    "/grantmakers/",
    "/grantmakers/tasks/",
    # "/grantmakers/tasks/<int:task_id>/",
    "/grantmakers/funder/GB-CHC-12345678/",
    "/grantmakers/funder/GB-CHC-12345678/change_status",
    "/grantmakers/funder/GB-CHC-12345678/tags",
    "/grantmakers/funder/GB-CHC-12345678/note",
    # "/grantmakers/funder/GB-CHC-12345678/note/<int:note_id>",
    "/grantmakers/funder/GB-CHC-12345678/funderyear",
    # "/grantmakers/funder/GB-CHC-12345678/funderyear/<int:funderyear_id>",
]


@pytest.mark.parametrize("url", GRANTMAKER_URLS)
def test_not_logged_in(client: Client, url: str):
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"


def test_index(client_logged_in: Client):
    response = client_logged_in.get("/grantmakers/")
    assert response.status_code == 200


def test_index_with_funder(client_logged_in: Client, funder: Funder):
    response = client_logged_in.get("/grantmakers/")
    assert response.status_code == 200
    assert funder.name in response.content.decode("utf-8")


def test_tasks(client_logged_in: Client):
    response = client_logged_in.get("/grantmakers/tasks/")
    assert response.status_code == 200


def test_tasks_with_task(client_logged_in: Client, task: CleaningStatus):
    response = client_logged_in.get("/grantmakers/tasks/")
    assert response.status_code == 200
    assert task.name in response.content.decode("utf-8")


def test_tasks_with_complex_task(
    client_logged_in: Client, complex_task: CleaningStatus
):
    response = client_logged_in.get("/grantmakers/tasks/")
    assert response.status_code == 200
    assert complex_task.name in response.content.decode("utf-8")
    assert "<span>0 / 1</span>" in response.content.decode("utf-8")


def test_task_not_exist(client_logged_in: Client):
    response = client_logged_in.get("/grantmakers/tasks/1234/")
    assert response.status_code == 404


def test_task_with_task(client_logged_in: Client, task: CleaningStatus):
    response = client_logged_in.get(f"/grantmakers/tasks/{task.id}")
    assert response.status_code == 200
    assert task.name in response.content.decode("utf-8")


def test_task_with_complex_task(client_logged_in: Client, complex_task: CleaningStatus):
    response = client_logged_in.get(f"/grantmakers/tasks/{complex_task.id}")
    assert response.status_code == 200
    assert complex_task.name in response.content.decode("utf-8")
    assert "<span>0 / 1</span>" in response.content.decode("utf-8")


def test_task_csv(client_logged_in: Client, complex_task: CleaningStatus):
    response = client_logged_in.get(f"/grantmakers/tasks/{complex_task.id}.csv")
    assert response.status_code == 200
    lines = response.content.decode("utf-8").strip().split("\n")
    assert len(lines) == 2


def test_funder_not_exist(client_logged_in: Client, requests_mock):
    requests_mock.get(
        "https://findthatcharity.uk/api/v1/organisations/GB-CHC-12345679",
        status_code=404,
    )
    response = client_logged_in.get("/grantmakers/funder/GB-CHC-12345679/")
    assert response.status_code == 200
    assert "Grantmaker: GB-CHC-12345679 Not Found" in response.content.decode("utf-8")


def test_funder_new(client_logged_in: Client):
    response = client_logged_in.get("/grantmakers/funder/new")
    assert response.status_code == 200
    assert "Add a new record" in response.content.decode("utf-8")


def test_funder_create_new(client_logged_in: Client):
    response = client_logged_in.post(
        "/grantmakers/funder/new",
        data={
            "org_id": "GB-CHC-12345679",
            "name_manual": "Test Funder 12345679",
            "status": "New",
        },
        follow=True,
    )
    assert response.status_code == 200
    assert "Test Funder 12345679" in response.content.decode("utf-8")

    funder = Funder.objects.get(org_id="GB-CHC-12345679")
    assert funder.name == "Test Funder 12345679"


def test_funder_new_check_api(client_logged_in: Client, requests_mock):
    requests_mock.get(
        "https://findthatcharity.uk/api/v1/organisations/GB-CHC-12345679",
        status_code=404,
    )
    response = client_logged_in.get(
        "/grantmakers/funder/new?org_id=GB-CHC-12345679", follow=True
    )
    assert response.status_code == 200
    assert (
        "Organisation not found in Find that Charity API for org_id GB-CHC-12345679"
        in response.content.decode("utf-8")
    )


def test_funder_with_funder(client_logged_in: Client, funder: Funder):
    response = client_logged_in.get(f"/grantmakers/funder/{funder.org_id}/")
    assert response.status_code == 200
    assert funder.name in response.content.decode("utf-8")
