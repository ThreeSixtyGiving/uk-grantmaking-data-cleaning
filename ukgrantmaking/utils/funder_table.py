from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from caradoc import FinancialYear
from django.utils.text import slugify

from ukgrantmaking.models import (
    Funder,
    FunderYear,
)


def funder_table(
    current_fy: FinancialYear,
    columns: list[str],
    effective_date: datetime,
    n: int = 100,
    sortby: str = "-cy_scale",
    tag_children: Optional[list[str]] = None,
    spending_threshold: int = 25_000,
    **filters,
):
    ascending = True
    if sortby.startswith("-"):
        sortby = sortby[1:]
        ascending = False

    agg_fields = [
        ("income", "Income"),
        ("spending", "Spending"),
        ("spending_grant_making", "Grant Making Spending"),
        ("spending_grant_making_institutions", "Grant Making Spending (Institutions)"),
        ("spending_grant_making_individuals", "Grant Making Spending (Individuals)"),
        ("total_net_assets", "Net Assets"),
        ("funds_endowment", "Endowment Funds"),
        ("employees", "Employees"),
    ]
    tags = [
        ("Living Wage Funder", "Living Wage Funder"),
        ("360Giving Publisher", "360Giving Publisher"),
        ("ACO", "ACO Member"),
    ]

    # fetch all the data
    funders = pd.DataFrame.from_records(
        Funder.objects.filter(**filters).values(
            "org_id",
            "name",
            "segment",
            "makes_grants_to_individuals",
            "included",
            "date_of_registration",
        )
    )
    cy_data = pd.DataFrame.from_records(
        FunderYear.objects.filter(
            financial_year=current_fy,
            date_added__lte=effective_date,
            funder__in=Funder.objects.filter(**filters).values_list(
                "org_id", flat=True
            ),
        )
        .order_by("funder_id", "-financial_year_end")
        .values(
            "funder_id",
            "financial_year_end",
            "notes",
            *[field for field, _ in agg_fields],
        ),
        columns=[
            "funder_id",
            "financial_year_end",
            "notes",
            *[field for field, _ in agg_fields],
        ],
    )
    py_data = pd.DataFrame.from_records(
        FunderYear.objects.filter(
            financial_year=current_fy - 1,
            date_added__lte=effective_date,
            funder__in=Funder.objects.filter(**filters).values_list(
                "org_id", flat=True
            ),
        )
        .order_by("funder_id", "-financial_year_end")
        .values(
            "funder_id",
            "financial_year_end",
            "notes",
            *[field for field, _ in agg_fields],
        ),
        columns=[
            "funder_id",
            "financial_year_end",
            "notes",
            *[field for field, _ in agg_fields],
        ],
    )

    cy_data["scale"] = cy_data["spending_grant_making"].fillna(cy_data["spending"])
    py_data["scale"] = py_data["spending_grant_making"].fillna(py_data["spending"])
    df = funders.join(
        cy_data.groupby("funder_id").agg(
            cy_income=(
                "income",
                lambda x: x.sum(min_count=1),
            ),
            cy_spending=(
                "spending",
                lambda x: x.sum(min_count=1),
            ),
            cy_spending_grant_making=(
                "spending_grant_making",
                lambda x: x.sum(min_count=1),
            ),
            cy_spending_grant_making_institutions=(
                "spending_grant_making_institutions",
                lambda x: x.sum(min_count=1),
            ),
            cy_spending_grant_making_individuals=(
                "spending_grant_making_individuals",
                lambda x: x.sum(min_count=1),
            ),
            cy_total_net_assets=(
                "total_net_assets",
                "first",
            ),
            cy_funds_endowment=(
                "funds_endowment",
                "first",
            ),
            cy_employees=(
                "employees",
                "first",
            ),
            cy_scale=(
                "scale",
                lambda x: x.sum(min_count=1),
            ),
            cy_notes=("notes", "first"),
        ),
        on="org_id",
        how="left",
    ).join(
        py_data.groupby("funder_id").agg(
            py_income=(
                "income",
                lambda x: x.sum(min_count=1),
            ),
            py_spending=(
                "spending",
                lambda x: x.sum(min_count=1),
            ),
            py_spending_grant_making=(
                "spending_grant_making",
                lambda x: x.sum(min_count=1),
            ),
            py_spending_grant_making_institutions=(
                "spending_grant_making_institutions",
                lambda x: x.sum(min_count=1),
            ),
            py_spending_grant_making_individuals=(
                "spending_grant_making_individuals",
                lambda x: x.sum(min_count=1),
            ),
            py_total_net_assets=(
                "total_net_assets",
                "first",
            ),
            py_funds_endowment=(
                "funds_endowment",
                "first",
            ),
            py_employees=(
                "employees",
                "first",
            ),
            py_scale=(
                "scale",
                lambda x: x.sum(min_count=1),
            ),
            py_notes=("notes", "first"),
        ),
        on="org_id",
        how="left",
    )

    df["cy_rank"] = (
        df[sortby]
        .rank(ascending=ascending, method="min", na_option="bottom")
        .astype(int)
    )
    df["py_rank"] = (
        df[sortby.replace("cy_", "py_")]
        .rank(ascending=ascending, method="min", na_option="bottom")
        .astype(int)
    )

    if spending_threshold is not None:
        df = df[
            df["cy_spending"].fillna(df["cy_spending_grant_making"])
            >= spending_threshold
        ]

    funder_tags = pd.DataFrame.from_records(
        Funder.tags.through.objects.filter(
            funder__in=Funder.objects.filter(**filters).values_list(
                "org_id", flat=True
            ),
        ).values(
            "funder_id",
            "fundertag",
            "fundertag__parent",
        )
    )
    for tag, _ in tags:
        df[slugify(tag).replace("-", "_")] = df["org_id"].isin(
            funder_tags[funder_tags["fundertag"] == tag]["funder_id"]
        )
    if tag_children:
        tag_children_df = funder_tags[
            funder_tags["fundertag__parent"].isin(tag_children)
        ]
        if not tag_children_df.empty:
            tag_categories = pd.crosstab(
                tag_children_df["funder_id"],
                tag_children_df["fundertag__parent"],
                values=tag_children_df["fundertag"],
                aggfunc=lambda x: "; ".join(x),
            )
            df = df.join(tag_categories, on="org_id", how="left")
            columns += tag_children

    df["segment"] = (
        df["segment"].fillna("Unknown").replace({"Wellcome Trust": "Family Foundation"})
    )
    df["notes"] = df["cy_notes"].fillna(df["py_notes"])

    for tag, tag_name in tags + [
        ("makes_grants_to_individuals", "Makes grants to individuals")
    ]:
        tag_field = slugify(tag).replace("-", "_")
        df[tag_field] = df[tag_field].map({True: "✓", False: ""})

    max_value = max(
        [df[f"cy_{field}"].max() for field, _ in agg_fields]
        + [df[f"py_{field}"].max() for field, _ in agg_fields]
    )
    scale_value = 1_000_000
    scale_suffix = "£m"
    if max_value < 10_000_000:
        scale_value = 1_000
        scale_suffix = "£k"
    elif max_value < 100_000:
        scale_value = 1
        scale_suffix = "£"

    for field, field_name in agg_fields:
        if field in ("employees",):
            df[f"cy_{field}"] = df[f"cy_{field}"].round(0)
            df[f"py_{field}"] = df[f"py_{field}"].round(0)
        else:
            df[f"cy_{field}"] = df[f"cy_{field}"].divide(scale_value)
            df[f"py_{field}"] = df[f"py_{field}"].divide(scale_value)

    return (
        df.sort_values(sortby, ascending=ascending, ignore_index=True)[columns][0:n]
        .rename(
            columns={
                "cy_rank": "#",
                "py_rank": "Rank (Previous year)",
                "org_id": "Org ID",
                "name": "Name",
                "segment": "Segment",
                "makes_grants_to_individuals": "Grants to Individuals",
                **{slugify(tag).replace("-", "_"): tag_name for tag, tag_name in tags},
                **{
                    f"cy_{field}": f"{field_name} ({scale_suffix})"
                    for field, field_name in agg_fields
                    if field != "employees"
                },
                **{
                    f"py_{field}": f"{field_name} ({scale_suffix} - Previous year)"
                    for field, field_name in agg_fields
                    if field != "employees"
                },
                "cy_employees": "Employees",
                "py_employees": "Employees (Previous year)",
                "notes": "Notes",
                "date_of_registration": "Date of registration",
            }
        )
        .replace({np.nan: None, pd.NA: None})
    )
