import pytest

from ukgrantmaking.models.funder import FunderTag
from ukgrantmaking.models.funder_utils import FunderSegment, RecordStatus

# urls:
GRANTMAKER_HTMX_URLS = [
    "/grantmakers/funder/GB-CHC-12345678/change_status",
    "/grantmakers/funder/GB-CHC-12345678/tags",
    "/grantmakers/funder/GB-CHC-12345678/note",
    # "/grantmakers/funder/GB-CHC-12345678/note/<int:note_id>",
    "/grantmakers/funder/GB-CHC-12345678/funderyear",
    # "/grantmakers/funder/GB-CHC-12345678/funderyear/<int:funderyear_id>",
]


@pytest.mark.parametrize("url", GRANTMAKER_HTMX_URLS)
def test_not_htmx(client_logged_in, url):
    response = client_logged_in.get(url)
    assert response.status_code == 400
    assert "This view is only accessible via htmx" in response.content.decode("utf-8")


def test_htmx_get_note(client_logged_in, funder, admin_user, check_log_entry):
    funder.notes.create(note="test note", added_by=admin_user)
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/note",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "test note" in response.content.decode("utf-8")
    assert check_log_entry(funder) is None


def test_htmx_add_note(client_logged_in, funder, admin_user, check_log_entry):
    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/note",
        {"note": "test note"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "test note" in response.content.decode("utf-8")

    # check the note was added to the funder
    funder.refresh_from_db()
    assert funder.notes.count() == 1
    assert funder.notes.first().note == "test note"
    assert funder.notes.first().added_by == admin_user
    assert check_log_entry(funder) is not None


def test_htmx_edit_note(client_logged_in, funder, admin_user, check_log_entry):
    note = funder.notes.create(note="test note", added_by=admin_user)

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/note/{note.id}",
        {"note": "changed this note"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "changed this note" in response.content.decode("utf-8")

    # check the note was added to the funder
    funder.refresh_from_db()
    assert funder.notes.count() == 1
    assert funder.notes.first().note == "changed this note"
    assert funder.notes.first().added_by == admin_user
    assert check_log_entry(funder) is not None


def test_htmx_get_tags(client_logged_in, funder, check_log_entry):
    funder.tags.set([])
    funder.tags.create(tag="Tag 1")
    funder.tags.create(tag="Tag X")
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/tags",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "Tag 1" in response.content.decode("utf-8")
    assert "Tag X" in response.content.decode("utf-8")

    funder.refresh_from_db()
    assert funder.tags.count() == 2
    assert check_log_entry(funder) is None


@pytest.mark.parametrize(
    "existing_tags,new_tags",
    [
        ([], ["Tag Z", "Tag X"]),
        (["Tag 1", "Tag X"], ["Tag Z", "Tag X"]),
        (["Tag 1", "Tag X"], ["Tag Z", "Tag Y"]),
        (["Tag 1", "Tag X"], ["Tag Z"]),
        (["Tag 1", "Tag X"], ["Tag X"]),
        (["Tag X"], ["Tag X"]),
        (["Tag 1"], ["Tag X"]),
        (["Tag 1", "Tag X"], ["Tag 1"]),
        (["Tag 1", "Tag X"], []),
        ([], []),
    ],
)
def test_htmx_edit_tags(
    client_logged_in, funder, existing_tags, new_tags, check_log_entry
):
    tags = []
    if existing_tags:
        for tag_name in existing_tags:
            tag, _ = FunderTag.objects.get_or_create(tag=tag_name)
            tags.append(tag)
    funder.tags.set(tags)
    funder.org_id = "GB-XI-12345678"
    funder.save()
    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/tags",
        {"tags": new_tags},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    # check the tags were added to the funder
    assert funder.tags.count() == len(new_tags)

    funder.current_year.refresh_from_db()
    for tag in new_tags:
        assert tag in response.content.decode("utf-8")
        assert funder.tags.filter(tag=tag).exists()
        assert funder.current_year.tags.filter(tag=tag).exists()
    for tag in existing_tags:
        if tag not in new_tags:
            assert tag not in response.content.decode("utf-8")
            assert not funder.tags.filter(tag=tag).exists()
            assert not funder.current_year.tags.filter(tag=tag).exists()

    assert check_log_entry(funder) is not None


def test_htmx_change_status_get(client_logged_in, funder, check_log_entry):
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/change_status",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 405
    assert "POST" in response.content.decode("utf-8")
    assert check_log_entry(funder) is None


@pytest.mark.parametrize("initial_status", [True, False])
@pytest.mark.parametrize(
    "action,field,new_status",
    [
        ("doesnt_make_grants_to_individuals", "makes_grants_to_individuals", False),
        ("makes_grants_to_individuals", "makes_grants_to_individuals", True),
        ("include", "included", True),
        ("exclude", "included", False),
    ],
)
def test_htmx_change_status_bool(
    client_logged_in, funder, initial_status, action, field, new_status, check_log_entry
):
    setattr(funder, field, initial_status)
    funder.save()

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/change_status",
        {"action": action},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    # check the funder status was changed
    funder.refresh_from_db()
    assert getattr(funder, field) == new_status
    assert getattr(funder.current_year, field) == new_status
    assert check_log_entry(funder) is not None


@pytest.mark.parametrize(
    "initial_status",
    [
        RecordStatus.CHECKED,
        RecordStatus.UNCHECKED,
        RecordStatus.FOR_REVIEW,
        RecordStatus.NEW,
    ],
)
@pytest.mark.parametrize(
    "action,new_status",
    [
        ("marked_as_checked", RecordStatus.CHECKED),
        ("marked_as_unchecked", RecordStatus.UNCHECKED),
        ("mark_for_review", RecordStatus.FOR_REVIEW),
    ],
)
def test_htmx_change_status_checked(
    client_logged_in,
    admin_user,
    funder,
    initial_status,
    action,
    new_status,
    check_log_entry,
):
    funder.current_year.checked = initial_status
    funder.current_year.save()

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/change_status",
        {"action": action},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    # check the funder status was changed
    funder.refresh_from_db()
    assert funder.current_year.checked == new_status
    assert funder.current_year.checked_on is not None
    assert funder.current_year.checked_by == admin_user
    assert check_log_entry(funder) is not None


@pytest.mark.parametrize(
    "existing_segment,new_segment",
    [
        (None, FunderSegment.DONOR_ADVISED_FUND),
        (FunderSegment.DONOR_ADVISED_FUND, FunderSegment.DONOR_ADVISED_FUND),
        (FunderSegment.ARMS_LENGTH_BODY, FunderSegment.DONOR_ADVISED_FUND),
    ],
)
def test_htmx_change_status_segment(
    client_logged_in, funder, existing_segment, new_segment, check_log_entry
):
    funder.segment = existing_segment
    funder.save()

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/change_status",
        {"action": "update_segment", "segment": new_segment.value},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert new_segment.value in response.content.decode("utf-8")
    assert new_segment.category.value in response.content.decode("utf-8")

    # check the funder status was changed
    funder.refresh_from_db()
    assert funder.segment == new_segment
    assert funder.current_year.segment == new_segment
    assert check_log_entry(funder) is not None


@pytest.mark.parametrize(
    "existing_name,new_name",
    [
        ("Test XYZ", "Jubilee Trust"),
        ("Jubilee Trust", "Jubilee Trust"),
    ],
)
def test_htmx_change_status_name(
    client_logged_in, funder, existing_name, new_name, check_log_entry
):
    funder.name_registered = existing_name
    funder.save()
    funder.refresh_from_db()
    assert funder.name_manual is None
    assert funder.name == existing_name

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/change_status",
        {"action": "change_name", "name": new_name},
        headers={"HX-Request": "true", "HX-Target": "funder-header"},
    )
    assert response.status_code == 200
    assert new_name in response.content.decode("utf-8")
    assert existing_name in response.content.decode("utf-8")

    # check the funder name was changed
    funder.refresh_from_db()
    assert funder.name_registered == existing_name
    assert funder.name_manual == new_name
    assert funder.name == new_name
    assert check_log_entry(funder) is not None
