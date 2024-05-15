import numpy as np
import pandas as pd
from caradoc import FinancialYear
from django.db import models

from ukgrantmaking.models import (
    FUNDER_CATEGORIES,
    Funder,
)


def funder_summary_by_size(current_fy: FinancialYear):
    result = (
        pd.DataFrame.from_records(
            Funder.objects.filter(
                included=True,
            )
            .values("segment")
            .annotate(
                zero_spend=models.Sum(
                    models.Case(
                        models.When(
                            models.Q(
                                funderyear__spending_grant_making=0,
                                funderyear__financial_year=current_fy,
                            )
                            | models.Q(
                                funderyear__spending_grant_making__isnull=True,
                                funderyear__financial_year=current_fy,
                            ),
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                under_100k=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__spending_grant_making__lt=100_000,
                            funderyear__spending_grant_making__gt=0,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _100k_1m=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__spending_grant_making__lt=1_000_000,
                            funderyear__spending_grant_making__gte=100_000,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _1m_10m=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__spending_grant_making__lt=10_000_000,
                            funderyear__spending_grant_making__gte=1_000_000,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _10m_100m=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__spending_grant_making__lt=100_000_000,
                            funderyear__spending_grant_making__gte=10_000_000,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                over_100m=models.Sum(
                    models.Case(
                        models.When(
                            funderyear__financial_year=current_fy,
                            funderyear__spending_grant_making__gte=100_000_000,
                            then=1,
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
            total=lambda x: x[
                [
                    "zero_spend",
                    "under_100k",
                    "_100k_1m",
                    "_1m_10m",
                    "_10m_100m",
                    "over_100m",
                ]
            ].sum(axis=1),
        )
        .rename(
            columns={
                "category": "Category",
                "segment": "Segment",
                "zero_spend": "Zero /unknown spend",
                "under_100k": "Under £100k",
                "_100k_1m": "£100k - £1m",
                "_1m_10m": "£1m - £10m",
                "_10m_100m": "£10m - £100m",
                "over_100m": "Over £100m",
                "total": "Total",
            }
        )
        .set_index(["Category", "Segment"])
        .sort_index()
        .replace({False: pd.NA, np.nan: pd.NA, True: 1, 0: pd.NA})
        .replace({pd.NA: None})
    )
    return result
