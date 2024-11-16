import pytest

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
def test_not_logged_in(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == f"/accounts/login/?next={url}"


def test_index(client_logged_in):
    response = client_logged_in.get("/grantmakers/")
    assert response.status_code == 200


def test_index_with_funder(client_logged_in, funder):
    response = client_logged_in.get("/grantmakers/")
    assert response.status_code == 200
    assert funder.name in response.content.decode("utf-8")


def test_tasks(client_logged_in):
    response = client_logged_in.get("/grantmakers/tasks/")
    assert response.status_code == 200


def test_tasks_with_task(client_logged_in, task):
    response = client_logged_in.get("/grantmakers/tasks/")
    assert response.status_code == 200
    assert task.name in response.content.decode("utf-8")


def test_tasks_with_complex_task(client_logged_in, complex_task):
    response = client_logged_in.get("/grantmakers/tasks/")
    assert response.status_code == 200
    assert complex_task.name in response.content.decode("utf-8")
    assert "<span>0 / 1</span>" in response.content.decode("utf-8")


def test_task_not_exist(client_logged_in):
    response = client_logged_in.get("/grantmakers/tasks/1234/")
    assert response.status_code == 404


def test_task_with_task(client_logged_in, task):
    response = client_logged_in.get(f"/grantmakers/tasks/{task.id}/")
    assert response.status_code == 200
    assert task.name in response.content.decode("utf-8")


def test_task_with_complex_task(client_logged_in, complex_task):
    response = client_logged_in.get(f"/grantmakers/tasks/{complex_task.id}/")
    assert response.status_code == 200
    assert complex_task.name in response.content.decode("utf-8")
    assert "<span>0 / 1</span>" in response.content.decode("utf-8")


def test_funder_not_exist(client_logged_in):
    response = client_logged_in.get("/grantmakers/funder/GB-CHC-12345679/")
    assert response.status_code == 404


def test_funder_with_funder(client_logged_in, funder):
    response = client_logged_in.get(f"/grantmakers/funder/{funder.org_id}/")
    assert response.status_code == 200
    assert funder.name in response.content.decode("utf-8")
