from datetime import datetime

import numpy as np
import pandas as pd
from django.db import models

from ukgrantmaking.models import (
    FUNDER_CATEGORIES,
    Funder,
)


def funder_trend_over_time(
    years: list[str],
    field: str,
    aggregation: models.Aggregate,
    effective_date: datetime,
):
    year_annotations = {}
    for year in years:
        year_annotations[year] = aggregation(
            models.Case(
                models.When(
                    funderyear__financial_year=year,
                    funderyear__date_added__lte=effective_date,
                    then=models.F(f"funderyear__{field}"),
                ),
                default=0,
                output_field=models.IntegerField(),
            )
        )
        year_annotations[f"{year}_count"] = models.Sum(
            models.Case(
                models.When(
                    **{
                        "funderyear__financial_year": year,
                        "funderyear__date_added__lte": effective_date,
                        f"funderyear__{field}__gt": 0,
                        "then": 1,
                    }
                ),
                default=0,
                output_field=models.IntegerField(),
            )
        )
    query = (
        Funder.objects.filter(
            included=True,
        )
        .values("segment")
        .annotate(**year_annotations)
    )
    trends_over_time = (
        pd.DataFrame.from_records(query)
        .assign(
            segment=lambda x: x["segment"].fillna("Unknown"),
            category=(lambda x: x["segment"].map(FUNDER_CATEGORIES).fillna("Unknown")),
        )
        .rename(
            columns={
                "category": "Category",
                "segment": "Segment",
            }
        )
        .set_index(["Category", "Segment"])
        .sort_index()
        .replace({False: pd.NA, np.nan: pd.NA, True: 1, 0: pd.NA})
        .replace({pd.NA: None})
    )
    for year in years:
        trends_over_time[year] = trends_over_time[year].divide(1_000_000).round(1)
        trends_over_time[f"{year} Count"] = trends_over_time[f"{year}_count"].astype(
            "int"
        )
        del trends_over_time[f"{year}_count"]
    return trends_over_time
