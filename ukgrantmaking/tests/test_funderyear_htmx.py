def test_funder_htmx_get_funderyear(client_logged_in, funder):
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{funder.latest_year.financial_years.first().id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "funder-year-edit" in response.content.decode("utf-8")


# @TODO Test creating a new funderyear


def test_not_htmx(client_logged_in, funder, check_log_entry):
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{funder.latest_year.financial_years.first().id}"
    )
    assert response.status_code == 400
    assert "This view is only accessible via htmx" in response.content.decode("utf-8")
    assert check_log_entry(funder) is None


def test_wrong_funderid(client_logged_in, funder, make_funder, check_log_entry):
    funder2 = make_funder(2)
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{funder2.latest_year.financial_years.first().id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 400
    assert "Invalid funderyear_id" in response.content.decode("utf-8")
    assert check_log_entry(funder) is None
    assert check_log_entry(funder2) is None


def test_delete_funderyear(client_logged_in, funder, check_log_entry):
    assert funder.latest_year.financial_years.count() == 1
    to_delete = funder.latest_year.financial_years.first()
    fye = to_delete.financial_year_end.strftime("%Y-%m-%d")

    response = client_logged_in.delete(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{to_delete.id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    funder.refresh_from_db()
    assert funder.latest_year.financial_years.count() == 0
    assert fye in check_log_entry(funder)[0].change_message


def test_edit_funderyear(client_logged_in, funder, check_log_entry):
    fy = funder.latest_year.financial_years.first()
    assert fy.spending_investment_registered is None
    assert fy.spending_investment_manual is None
    assert fy.spending_investment is None

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{fy.id}",
        data={"spending_investment-cy": 1_000},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert (
        fy.financial_year_end.strftime("%Y-%m-%d")
        in check_log_entry(funder)[0].change_message
    )

    fy.refresh_from_db()
    assert fy.spending_investment_registered is None
    assert fy.spending_investment_manual == 1_000
    assert fy.spending_investment == 1_000


def test_edit_funderyear_add_note(client_logged_in, funder, check_log_entry):
    fy = funder.latest_year.financial_years.first()
    assert fy.notes is None

    note = "Test note"

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{fy.id}",
        data={"spending_investment-cy": 1_000, "note": note},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    fy.refresh_from_db()
    assert fy.notes == note
    assert (
        fy.financial_year_end.strftime("%Y-%m-%d")
        in check_log_entry(funder)[0].change_message
    )


def test_edit_funderyear_py(client_logged_in, funder_with_py, check_log_entry):
    fy = funder_with_py.latest_year.financial_years.first()
    assert fy.spending_investment_registered is None
    assert fy.spending_investment_manual is None
    assert fy.spending_investment is None

    fy_py = funder_with_py.financial_years.last().financial_years.first()
    assert fy_py.spending_investment_registered is None
    assert fy_py.spending_investment_manual is None
    assert fy_py.spending_investment is None

    response = client_logged_in.post(
        f"/grantmakers/funder/{funder_with_py.org_id}/funderyear/{fy.id}",
        data={"spending_investment-cy": 1_000, "spending_investment-py": 2_345},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200

    fy.refresh_from_db()
    assert fy.spending_investment_registered is None
    assert fy.spending_investment_manual == 1_000
    assert fy.spending_investment == 1_000

    fy_py.refresh_from_db()
    assert fy_py.spending_investment_registered is None
    assert fy_py.spending_investment_manual == 2_345
    assert fy_py.spending_investment == 2_345

    log_entries = check_log_entry(funder_with_py)
    found_fy = False
    found_fy_py = False
    for log_entry in log_entries:
        if fy.financial_year_end.strftime("%Y-%m-%d") in log_entry.change_message:
            found_fy = True
        if fy_py.financial_year_end.strftime("%Y-%m-%d") in log_entry.change_message:
            found_fy_py = True
    assert found_fy
    assert found_fy_py
