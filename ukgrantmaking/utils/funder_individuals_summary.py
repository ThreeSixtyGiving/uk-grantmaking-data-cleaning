import numpy as np
import pandas as pd
from caradoc import FinancialYear
from django.db import models

from ukgrantmaking.models import (
    FUNDER_CATEGORIES,
    Funder,
)


def funder_individuals_summary(current_fy: FinancialYear):
    summary_individuals = (
        pd.DataFrame.from_records(
            Funder.objects.filter(
                included=True,
                makes_grants_to_individuals=True,
            )
            .values("segment")
            .annotate(
                individuals=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            makes_grants_to_individuals=True,
                            then=models.Value(1),
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                individuals_with_data=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__spending_grant_making_individuals__gt=0,
                            makes_grants_to_individuals=True,
                            then=models.Value(1),
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                individuals_and_institutions_with_data=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__spending_grant_making_individuals__gt=0,
                            funderyear__spending_grant_making_institutions__gt=0,
                            makes_grants_to_individuals=True,
                            then=models.Value(1),
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                grantmaking_to_individuals=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            then=models.F(
                                "funderyear__spending_grant_making_individuals"
                            ),
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
                "grantmaking_to_individuals": "Grants to individuals (£m)",
                "individuals_with_data": "Largest orgs with data",
                "individuals_and_institutions_with_data": "Orgs that also make grants to institutions",
                "individuals": "No. of Grantmakers that make grants to individuals",
            }
        )
        .set_index(["Category", "Segment"])
        .sort_index()
        .replace({False: pd.NA, np.nan: pd.NA, True: 1})
        .replace({pd.NA: None})
    )
    summary_individuals.loc[("Total", "Total"), :] = summary_individuals.sum(axis=0)
    return summary_individuals
