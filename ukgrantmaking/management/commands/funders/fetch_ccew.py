import djclick as click
import pandas as pd

from ukgrantmaking.models.funder_year import FunderYear

FIELDS_TO_UPDATE = [
    ("Employees: Number of permanent employees", "employees_permanent_registered"),
    (
        "Employees: Number of employees on fixed-terms contracts",
        "employees_fixedterm_registered",
    ),
    ("Employees: Number of self-employed people", "employees_selfemployed_registered"),
    ("Income from investments", "income_investment_registered"),
    (
        "Grant making: Value of grants made to individuals",
        "spending_grant_making_individuals_registered",
    ),
    (
        "Grant making: Value of grants made to other charities",
        "spending_grant_making_institutions_charitable_registered",
    ),
    (
        "Grant making: Value of grants made to other organisations that are not charities",
        "spending_grant_making_institutions_noncharitable_registered",
    ),
]


@click.command()
@click.argument("file")
@click.option("--sheet", default="Sheet1")
@click.option("--skip-rows", default=0, type=int)
@click.option("--debug", is_flag=True, default=False)
def ccew(file, sheet: str, skip_rows: int = 0, debug: bool = False):
    click.secho("Opening {}".format(file), fg="green")
    df = pd.read_excel(file, sheet_name=sheet, skiprows=skip_rows)
    click.secho("{:,.0f} rows in datafile".format(len(df)), fg="green")

    # for employee fields, replace "0 - 2" with None
    for field_name, _ in FIELDS_TO_UPDATE:
        if field_name.startswith("Employees"):
            df[field_name] = pd.to_numeric(df[field_name].replace("0 - 2", pd.NA))

    if debug:
        df = df.sample(1000)
    updates = []
    values = {}
    org_ids = set()
    fyes = set()
    with click.progressbar(
        df.iterrows(),
        length=len(df),
        label="Updating finances from CCEW data",
    ) as bar:
        for index, row in bar:
            org_id = f'GB-CHC-{row["Registered charity number"]:.0f}'
            fye = row["fin_period_end_date"].to_pydatetime().date()
            org_ids.add(org_id)
            fyes.add(fye)
            values[(org_id, fye)] = row

    qs = FunderYear.objects.filter(
        funder_financial_year__funder_id__in=org_ids,
        financial_year_end__in=fyes,
    ).select_related("funder_financial_year")
    with click.progressbar(
        qs,
        length=qs.count(),
        label="Fetching existing rows from database",
    ) as bar:
        for funder_year in bar:
            try:
                row = values[
                    (
                        funder_year.funder_financial_year.funder_id,
                        funder_year.financial_year_end,
                    )
                ]
            except KeyError:
                continue

            employees = None
            for field_name, field in FIELDS_TO_UPDATE:
                if not pd.isna(row[field_name]):
                    setattr(funder_year, field, row[field_name])
                    if field.startswith("employees"):
                        if employees is None:
                            employees = 0
                        employees += int(row[field_name])

            if employees is not None and funder_year.employees is None:
                funder_year.employees_registered = employees

            updates.append(funder_year)

    years_updated = FunderYear.objects.bulk_update(
        updates,
        [f[1] for f in FIELDS_TO_UPDATE] + ["employees_registered"],
        batch_size=500,
    )

    click.secho(
        f"Updated {years_updated} charity financial years for funders", fg="green"
    )
