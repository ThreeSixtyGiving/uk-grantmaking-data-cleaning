import pytest


def test_funder_htmx_get_funderyear(client_logged_in, funder):
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{funder.current_year.funder_years.first().id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "funder-year-edit" in response.content.decode("utf-8")


# @TODO Test creating a new funderyear


def test_not_htmx(client_logged_in, funder, check_log_entry):
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{funder.current_year.funder_years.first().id}"
    )
    assert response.status_code == 400
    assert "This view is only accessible via htmx" in response.content.decode("utf-8")
    assert check_log_entry(funder) is None


def test_wrong_funderid(client_logged_in, funder, make_funder, check_log_entry):
    funder2 = make_funder(2)
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{funder2.current_year.funder_years.first().id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 400
    assert "Invalid funderyear_id" in response.content.decode("utf-8")
    assert check_log_entry(funder) is None
    assert check_log_entry(funder2) is None


def test_delete_funderyear(client_logged_in, funder, check_log_entry):
    assert funder.current_year.funder_years.count() == 1
    to_delete = funder.current_year.funder_years.first()
    fye = to_delete.financial_year_end.strftime("%Y-%m-%d")

    response = client_logged_in.delete(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{to_delete.id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    funder.refresh_from_db()
    assert funder.current_year.funder_years.count() == 0
    assert fye in check_log_entry(funder)[0].change_message


@pytest.mark.parametrize("initial_value_cy", [None, 10_000, 0, 1_000])
@pytest.mark.parametrize(
    "new_value_cy,expected_value_cy",
    [
        (1_000, 1_000),
        ("1000", 1_000),
        ("1,000", 1_000),
        ("", None),
        ("0", 0),
    ],
)
def test_edit_funderyear_cy(
    client_logged_in,
    funder,
    check_log_entry,
    initial_value_cy,
    new_value_cy,
    expected_value_cy,
):
    fy = funder.current_year.funder_years.first()
    if initial_value_cy is not None:
        fy.spending_investment_manual = initial_value_cy
        fy.save()
        fy.refresh_from_db()
    assert fy.spending_investment_registered is None
    assert fy.spending_investment_manual == initial_value_cy
    assert fy.spending_investment == initial_value_cy

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{fy.id}",
        data={"spending_investment-cy": new_value_cy},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    fy.refresh_from_db()
    assert fy.spending_investment_registered is None
    assert fy.spending_investment_manual == expected_value_cy
    assert fy.spending_investment == expected_value_cy

    assert fy.funder_financial_year.spending_investment == expected_value_cy

    logs = check_log_entry(funder)

    if expected_value_cy == initial_value_cy:
        assert logs is None
    else:
        assert fy.financial_year_end.strftime("%Y-%m-%d") in logs[0].change_message


@pytest.mark.parametrize("initial_value_cy", [None, 10_000, 0])
@pytest.mark.parametrize("initial_value_py", [None, 10_000, 0])
@pytest.mark.parametrize(
    "new_value_cy,new_value_py,expected_value_cy,expected_value_py",
    [
        (1_000, 2_345, 1_000, 2_345),
        ("1000", "2345", 1_000, 2_345),
        ("1,000", "2,345", 1_000, 2_345),
        ("", "2,345", None, 2_345),
        ("0", "2,345", 0, 2_345),
    ],
)
def test_edit_funderyear_py(
    client_logged_in,
    funder_with_py,
    check_log_entry,
    initial_value_cy,
    initial_value_py,
    new_value_cy,
    new_value_py,
    expected_value_cy,
    expected_value_py,
):
    fy = funder_with_py.current_year.funder_years.first()
    if initial_value_cy is not None:
        fy.spending_investment_manual = initial_value_cy
        fy.save()
        fy.refresh_from_db()
    assert fy.spending_investment_registered is None
    assert fy.spending_investment_manual == initial_value_cy
    assert fy.spending_investment == initial_value_cy

    fy_py = (
        funder_with_py.funder_financial_years.exclude(
            financial_year=funder_with_py.current_year.financial_year
        )
        .order_by("-financial_year")
        .first()
        .funder_years.first()
    )
    if initial_value_py is not None:
        fy_py.spending_investment_manual = initial_value_py
        fy_py.save()
        fy_py.refresh_from_db()
    assert fy_py.spending_investment_registered is None
    assert fy_py.spending_investment_manual == initial_value_py
    assert fy_py.spending_investment == initial_value_py

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder_with_py.org_id}/funderyear/{fy.id}",
        data={
            "spending_investment-cy": new_value_cy,
            "spending_investment-py": new_value_py,
        },
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    fy.refresh_from_db()
    assert fy.spending_investment_registered is None
    assert fy.spending_investment_manual == expected_value_cy
    assert fy.spending_investment == expected_value_cy
    assert fy.funder_financial_year.spending_investment == expected_value_cy

    fy_py.refresh_from_db()
    assert fy_py.spending_investment_registered is None
    assert fy_py.spending_investment_manual == expected_value_py
    assert fy_py.spending_investment == expected_value_py
    assert fy_py.funder_financial_year.spending_investment == expected_value_py

    log_entries = check_log_entry(funder_with_py)
    found_fy = False
    found_fy_py = False
    for log_entry in log_entries:
        if fy.financial_year_end.strftime("%Y-%m-%d") in log_entry.change_message:
            found_fy = True
        if fy_py.financial_year_end.strftime("%Y-%m-%d") in log_entry.change_message:
            found_fy_py = True
    assert found_fy == (expected_value_cy != initial_value_cy)
    assert found_fy_py == (expected_value_py != initial_value_py)


def test_edit_funderyear_add_note(client_logged_in, funder, check_log_entry):
    fy = funder.current_year.funder_years.first()
    assert fy.notes.count() == 0

    note = "Test note"

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{fy.id}",
        data={"spending_investment-cy": 1_000, "note": note},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    fy.refresh_from_db()
    assert fy.notes.count() == 1
    assert fy.notes.first().note == note
    assert (
        fy.financial_year_end.strftime("%Y-%m-%d")
        in check_log_entry(funder)[0].change_message
    )
