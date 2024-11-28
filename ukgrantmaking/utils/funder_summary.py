from datetime import datetime

import numpy as np
import pandas as pd
from caradoc import FinancialYear
from django.db import models

from ukgrantmaking.models.funder import Funder
from ukgrantmaking.models.funder_utils import FUNDER_CATEGORIES


def funder_summary(current_fy: FinancialYear, effective_date: datetime):
    result = (
        pd.DataFrame.from_records(
            Funder.objects.filter(
                included=True,
            )
            .values("segment")
            .annotate(
                count=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__date_added__lte=effective_date,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                income=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__date_added__lte=effective_date,
                            then=models.F("funderyear__income"),
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                spending=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__date_added__lte=effective_date,
                            then=models.F("funderyear__spending"),
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                grantmaking=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__date_added__lte=effective_date,
                            then=models.F("funderyear__spending_grant_making"),
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                grantmaking_to_individuals=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__date_added__lte=effective_date,
                            then=models.F(
                                "funderyear__spending_grant_making_individuals"
                            ),
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                individuals=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__date_added__lte=effective_date,
                            makes_grants_to_individuals=True,
                            then=models.Value(1),
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
            )
        )
        .assign(
            segment=lambda x: x["segment"].fillna("Unknown"),
            category=lambda x: x["segment"].map(FUNDER_CATEGORIES).fillna("Unknown"),
            income=lambda x: x["income"].divide(1_000_000).round(1),
            spending=lambda x: x["spending"].divide(1_000_000).round(1),
            grantmaking=lambda x: x["grantmaking"].divide(1_000_000).round(1),
            grantmaking_to_individuals=lambda x: x["grantmaking_to_individuals"]
            .divide(1_000_000)
            .round(1),
        )
        .rename(
            columns={
                "category": "Category",
                "segment": "Segment",
                "count": "Number of grantmakers",
                "income": "Total income",
                "spending": "Total spending",
                "grantmaking": "Spending on grants",
                "grantmaking_to_individuals": "Grants to individuals",
                "individuals": "No. of Grantmakers that make grants to individuals",
            }
        )
        .set_index(["Category", "Segment"])
        .sort_index()
        .replace({False: pd.NA, np.nan: pd.NA, True: 1})
        .replace({pd.NA: None})
    )
    result.loc[("Total", "Total"), :] = result.sum(axis=0)
    return result
