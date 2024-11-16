def test_funder_htmx_get_funderyear(client_logged_in, funder):
    response = client_logged_in.get(
        f"/grantmakers/funder/{funder.org_id}/funderyear/{funder.latest_year.financial_years.first().id}",
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "funder-year-edit" in response.content.decode("utf-8")


# @TODO Lots more tests to write here
