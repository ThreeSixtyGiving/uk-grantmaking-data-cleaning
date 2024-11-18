import pytest


@pytest.mark.django_db
def test_funder_successor(funder, funder_with_py):
    def get_fys():
        funder_fys = []
        for funder_financial_year in funder.funder_financial_years.all():
            for funder_year in funder_financial_year.funder_years.all():
                funder_fys.append(funder_year)
        successor_fys = []
        for funder_financial_year in funder_with_py.funder_financial_years.all():
            for funder_year in funder_financial_year.funder_years.all():
                successor_fys.append(funder_year)
        return funder_fys, successor_fys

    funder_fys, successor_fys = get_fys()
    assert len(funder_fys) == 1
    assert len(successor_fys) == 2

    funder.successor = funder_with_py
    funder.save()

    funder.refresh_from_db()
    funder_with_py.refresh_from_db()

    assert funder.successor == funder_with_py
    assert funder.pk in funder_with_py.predecessors.values_list("pk", flat=True)

    funder_fys, successor_fys = get_fys()
    assert len(funder_fys) == 0
    assert len(successor_fys) == 3


@pytest.mark.django_db
def test_funder_successor_2(funder, funder_with_py):
    def get_fys():
        funder_fys = []
        for funder_financial_year in funder.funder_financial_years.all():
            for funder_year in funder_financial_year.funder_years.all():
                funder_fys.append(funder_year)
        successor_fys = []
        for funder_financial_year in funder_with_py.funder_financial_years.all():
            for funder_year in funder_financial_year.funder_years.all():
                successor_fys.append(funder_year)
        return funder_fys, successor_fys

    funder_fys, successor_fys = get_fys()
    assert len(funder_fys) == 1
    assert len(successor_fys) == 2

    funder_with_py.successor = funder
    funder_with_py.save()

    funder.refresh_from_db()
    funder_with_py.refresh_from_db()

    assert funder_with_py.successor == funder
    assert funder_with_py.pk in funder.predecessors.values_list("pk", flat=True)

    funder_fys, successor_fys = get_fys()
    assert len(funder_fys) == 3
    assert len(successor_fys) == 0
