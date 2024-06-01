from datetime import datetime

import numpy as np
import pandas as pd
from caradoc import FinancialYear
from django.db import models

from ukgrantmaking.models import (
    Funder,
)
from ukgrantmaking.utils.funder_table import funder_table


def funder_over_time(
    current_fy: FinancialYear,
    columns: list[tuple[str, str, models.Aggregate]],
    effective_date: datetime,
    n: int = 100,
    n_years: int = 5,
    sortby: str = "-cy_scale",
    **filters,
):
    orgs = funder_table(
        current_fy,
        [
            "org_id",
        ],
        effective_date=effective_date,
        sortby=sortby,
        **filters,
        n=n,
    )["Org ID"].tolist()
    years = [str(fy) for fy in current_fy.previous_n_years(n_years - 1)][::-1]
    year_annotations = {}
    column_renames = {}
    for field, field_name, aggregation in columns:
        for year in years:
            year_annotations[f"{field}_{year}"] = aggregation(
                models.Case(
                    models.When(
                        funderyear__financial_year=year,
                        funderyear__date_added__lte=effective_date,
                        then=models.F(f"funderyear__{field}"),
                    ),
                    default=None,
                    output_field=models.IntegerField(),
                )
            )
            column_renames[f"{field}_{year}"] = f"{field_name} {year}"
    trends_query = (
        Funder.objects.filter(
            org_id__in=orgs,
        )
        .values("org_id", "name", "segment")
        .annotate(**year_annotations)
    )
    trends_over_time = (
        pd.DataFrame.from_records(trends_query)
        .rename(
            columns={
                "org_id": "Org ID",
                "name": "Funder name",
                "segment": "Segment",
                **column_renames,
            }
        )
        .set_index("Org ID")
        .loc[orgs, :]
    )
    for year in years:
        for field, field_name, aggregation in columns:
            trends_over_time[f"{field_name} {year}"] = (
                trends_over_time[f"{field_name} {year}"].divide(1_000_000).round(1)
            )
    trends_over_time = trends_over_time.replace({False: pd.NA, np.nan: pd.NA}).replace(
        {pd.NA: None}
    )
    return trends_over_time
