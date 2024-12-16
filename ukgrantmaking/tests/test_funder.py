import pytest


def get_fys(funder, successor):
    return list(funder.funder_years()), list(successor.funder_years())


@pytest.mark.django_db
def test_funder_successor(funder, funder_with_py):
    funder_fys, successor_fys = get_fys(funder, funder_with_py)
    assert len(funder_fys) == 1
    assert len(successor_fys) == 2

    funder.successor = funder_with_py
    funder.save()

    funder.refresh_from_db()
    funder_with_py.refresh_from_db()

    assert funder.successor == funder_with_py
    assert funder.pk in funder_with_py.predecessors.values_list("pk", flat=True)

    funder_fys, successor_fys = get_fys(funder, funder_with_py)
    assert len(funder_fys) == 0
    assert len(successor_fys) == 3

    # check "new_funder_financial_year_id" is set correctly
    assert len([fy for fy in successor_fys if fy.new_funder_financial_year_id]) == 1


@pytest.mark.django_db
def test_funder_successor_2(funder, funder_with_py):
    funder_fys, successor_fys = get_fys(funder_with_py, funder)
    assert len(funder_fys) == 2
    assert len(successor_fys) == 1

    funder_with_py.successor = funder
    funder_with_py.save()

    funder.refresh_from_db()
    funder_with_py.refresh_from_db()

    assert funder_with_py.successor == funder
    assert funder_with_py.pk in funder.predecessors.values_list("pk", flat=True)

    funder_fys, successor_fys = get_fys(funder_with_py, funder)
    assert len(funder_fys) == 0
    assert len(successor_fys) == 3

    # check "new_funder_financial_year_id" is set correctly
    assert len([fy for fy in successor_fys if fy.new_funder_financial_year_id]) == 2
