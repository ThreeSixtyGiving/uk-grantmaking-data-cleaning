import pandas as pd
from caradoc import FinancialYear
from django.db import models

from ukgrantmaking.models.funder import FUNDER_CATEGORIES
from ukgrantmaking.models.grant import Grant

DEFAULT_COLUMNS = [
    "grant_id",
    "funding_organisation_id",
    "funding_organisation_name",
    "recipient_organisation_id",
    "recipient_organisation_name",
    "title",
    "amount_awarded_GBP",
    "award_date",
    "regrant_type",
    "inclusion",
]


def grant_table(
    current_fy: FinancialYear,
    columns: list[str] = DEFAULT_COLUMNS,
    n: int = 100,
    sortby: str = "-amount_awarded_GBP",
    **filters,
):
    result = (
        Grant.objects.filter(
            award_date__gte=current_fy.start_date,
            award_date__lte=current_fy.end_date,
        )
        .filter(**filters)
        .order_by(sortby)
        .values(*columns)
    )
    if n:
        result = result[0:n]

    result_df = pd.DataFrame(result, columns=columns)
    if "amount_awarded_GBP" in result_df.columns:
        result_df["amount_awarded_GBP"] = result_df["amount_awarded_GBP"].astype(int)
    return result_df


summary_columns = {
    "category": "Category",
    "funder__segment": "Segment",
    "count": "Grants",
    "amount": "Grant Amount (£)",
    "mean_amount": "Mean Grant Amount (£)",
    "recipients": "Recipients",
    "funders": "Funders",
    "grants_with_orgid": "Grants with OrgID",
    "grants_missing_orgid": "Grants missing OrgID",
}


def grant_summary(
    current_fy: FinancialYear,
    **filters,
):
    summary = (
        pd.DataFrame(
            Grant.objects.filter(
                award_date__gte=current_fy.start_date,
                award_date__lte=current_fy.end_date,
            )
            .filter(**filters)
            .values("funder__segment")
            .annotate(
                count=models.Count("grant_id"),
                amount=models.Sum("amount_awarded_GBP"),
                mean_amount=models.Avg("amount_awarded_GBP"),
                recipients=models.Count(
                    models.functions.Coalesce(
                        "recipient_id",
                        "recipient_organisation_id",
                        "recipient_individual_id",
                    ),
                    distinct=True,
                ),
                funders=models.Count(
                    models.functions.Coalesce(
                        "funder_id",
                        "funding_organisation_id",
                    ),
                    distinct=True,
                ),
                grants_with_orgid=models.Count(
                    "grant_id", filter=~models.Q(recipient__org_id_schema="UKG")
                ),
                grants_missing_orgid=models.Count(
                    "grant_id", filter=models.Q(recipient__org_id_schema="UKG")
                ),
            )
        )
        .assign(
            amount=lambda x: x["amount"].astype(float),
            mean_amount=lambda x: x["mean_amount"].astype(float),
            category=lambda x: (
                x["funder__segment"].map(FUNDER_CATEGORIES).fillna("Unknown")
            ),
        )[summary_columns.keys()]
        .rename(columns=summary_columns)
        .set_index(["Category", "Segment"])
        .sort_index()
    )
    return summary


def grant_by_size(
    current_fy: FinancialYear,
    amount_field="amount_awarded_GBP",
    **filters,
):
    result = (
        pd.DataFrame(
            Grant.objects.filter(
                award_date__gte=current_fy.start_date,
                award_date__lte=current_fy.end_date,
            )
            .filter(**filters)
            .values("funder__segment")
            .annotate(
                zero_grants=models.Sum(
                    models.Case(
                        models.When(
                            **{
                                f"{amount_field}__lte": 0,
                                "then": 1,
                            }
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                under_1k=models.Sum(
                    models.Case(
                        models.When(
                            **{
                                f"{amount_field}__gt": 0,
                                f"{amount_field}__lte": 1_000,
                                "then": 1,
                            }
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _1k_10k=models.Sum(
                    models.Case(
                        models.When(
                            **{
                                f"{amount_field}__gt": 1_000,
                                f"{amount_field}__lte": 10_000,
                                "then": 1,
                            }
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _10k_100k=models.Sum(
                    models.Case(
                        models.When(
                            **{
                                f"{amount_field}__gt": 10_000,
                                f"{amount_field}__lte": 100_000,
                                "then": 1,
                            }
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _100k_1m=models.Sum(
                    models.Case(
                        models.When(
                            **{
                                f"{amount_field}__gt": 100_000,
                                f"{amount_field}__lte": 1_000_000,
                                "then": 1,
                            }
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                over_1m=models.Sum(
                    models.Case(
                        models.When(
                            **{
                                f"{amount_field}__gt": 1_000_000,
                                "then": 1,
                            }
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
            )
        )
        .assign(
            funder__segment=lambda x: x["funder__segment"].fillna("Unknown"),
            category=lambda x: (
                x["funder__segment"].map(FUNDER_CATEGORIES).fillna("Unknown")
            ),
            total=lambda x: x[
                [
                    "zero_grants",
                    "under_1k",
                    "_1k_10k",
                    "_10k_100k",
                    "_100k_1m",
                    "over_1m",
                ]
            ].sum(axis=1),
        )
        .rename(
            columns={
                "category": "Category",
                "funder__segment": "Segment",
                "zero_grants": "Zero /unknown grants",
                "under_1k": "Under £1k",
                "_1k_10k": "£1,001 to £10k",
                "_10k_100k": "£11k to £100k",
                "_100k_1m": "£101k to £1m",
                "over_1m": "Over £1m",
                "total": "Total",
            }
        )
        .set_index(["Category", "Segment"])
        .sort_index()
        .replace({False: pd.NA, True: 1, 0: pd.NA})
        .replace({pd.NA: None})
    )
    return result
