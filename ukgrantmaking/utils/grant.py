import json

import pandas as pd
from caradoc import FinancialYear
from django.db import models

from ukgrantmaking.models.funder import FUNDER_CATEGORIES
from ukgrantmaking.models.grant import Grant, GrantRecipientYear

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

SEGMENT_ORDER = [
    ("Grantmaker", "Community Foundation"),
    ("Grantmaker", "Corporate Foundation"),
    ("Grantmaker", "Family Foundation"),
    ("Grantmaker", "Fundraising Grantmaker"),
    ("Grantmaker", "General grantmaker"),
    ("Grantmaker", "Government/Lottery Endowed"),
    ("Grantmaker", "Member/Trade Funded"),
    # ("Grantmaker", "Small grantmaker"),
    ("Grantmaker", "Wellcome Trust"),
    ("Grantmaker", "Total"),
    ("Lottery", "Lottery Distributor"),
    ("Charity", "Charity"),
    ("Charity", "NHS/Hospital Foundation"),
    ("Charity", "Total"),
    ("Government", "Local"),
    ("Government", "Central"),
    ("Government", "Devolved"),
    ("Government", "Arms Length Body"),
    ("Government", "Total"),
    ("Other", "Donor Advised Fund"),
    ("Unknown", "Unknown"),
    ("Total", "Total"),
]

AMOUNT_AWARDED_BINS = [
    float("-inf"),
    1,
    1_000,
    10_000,
    100_000,
    1_000_000,
    float("inf"),
]
AMOUNT_AWARDED_BINS_LABELS = [
    "Negative / zero",
    "Under £1k",
    "£1k to £10k",
    "£10k to £100k",
    "£100k to £1m",
    "Over £1m",
]
INCOME_BINS = [
    float("-inf"),
    0,
    10_000,
    100_000,
    1_000_000,
    10_000_000,
    float("inf"),
]
INCOME_BINS_LABELS = [
    "Negative / zero",
    "Under £01k",
    "£10k to £100k",
    "£100k to £1m",
    "£1m to £10m",
    "Over £10m",
]
DURATION_BINS = [
    0,
    6,
    12,
    35,
    float("inf"),
]
DURATION_BINS_LABELS = [
    "Up to 6 months",
    "7-12 months",
    "18 months - 2 years",
    "3 years and more",
]

AGG_COLUMNS = {
    "Grants": ("recipient_id", "count"),
    "Grant amount": ("amount_awarded_GBP", "sum"),
    "Mean amount": ("amount_awarded_GBP", "mean"),
    "Min amount": ("amount_awarded_GBP", "min"),
    "Lower quartile amount": ("amount_awarded_GBP", lambda x: x.quantile(0.25)),
    "Median amount": ("amount_awarded_GBP", "median"),
    "Upper quartile amount": ("amount_awarded_GBP", lambda x: x.quantile(0.75)),
    "Max amount": ("amount_awarded_GBP", "max"),
    "Recipients": ("recipient_id", "nunique"),
    "Funders": ("funder_id", "nunique"),
    "First grant": ("award_date", "min"),
    "Last grant": ("award_date", "max"),
    "Min duration": ("planned_dates_duration", "min"),
    "Max duration": ("planned_dates_duration", "max"),
    "Median duration": ("planned_dates_duration", "median"),
    "Grant amount (Adjusted)": ("annual_amount", "sum"),
    "Mean amount (Adjusted)": ("annual_amount", "mean"),
    "Min amount (Adjusted)": ("annual_amount", "min"),
    "Lower quartile amount (Adjusted)": (
        "annual_amount",
        lambda x: x.quantile(0.25),
    ),
    "Median amount (Adjusted)": ("annual_amount", "median"),
    "Upper quartile amount (Adjusted)": (
        "annual_amount",
        lambda x: x.quantile(0.75),
    ),
    "Max amount (Adjusted)": ("annual_amount", "max"),
}


def get_all_grants(current_fy: FinancialYear):
    columns = [
        "grant_id",
        "funding_organisation_id",
        "funding_organisation_name",
        "recipient_organisation_id",
        "recipient_organisation_name",
        "title",
        "amount_awarded_GBP",
        "annual_amount",
        "planned_dates_duration",
        "award_date",
        "regrant_type",
        "inclusion",
        "funder__segment",
        "recipient__org_id_schema",
        "recipient__scale",
        "recipient_individual_primary_grant_reason",
        "recipient_individual_secondary_grant_reason",
        "recipient_individual_grant_purpose",
    ]
    result = (
        pd.DataFrame(
            Grant.objects.filter(
                award_date__gte=current_fy.start_date,
                award_date__lte=current_fy.end_date,
                inclusion__in=[
                    Grant.InclusionStatus.INCLUDED,
                    Grant.InclusionStatus.UNSURE,
                ],
            )
            .values(*columns)
            .annotate(
                recipient_type=models.functions.Coalesce(
                    "recipient_type_manual",
                    "recipient_type",
                ),
                recipient_id=models.functions.Coalesce(
                    "recipient_id",
                    "recipient_organisation_id",
                    "recipient_individual_id",
                ),
                funder_id=models.functions.Coalesce(
                    "funder_id",
                    "funding_organisation_id",
                ),
                funder_name=models.functions.Coalesce(
                    "funder__name",
                    "funding_organisation_name",
                ),
            )
        )
        .assign(
            funder__segment=lambda x: x["funder__segment"].fillna("Unknown"),
            amount_awarded_GBP=lambda x: x["amount_awarded_GBP"].astype(float),
            annual_amount=lambda x: x["annual_amount"].astype(float),
            recipient__org_id_schema=lambda x: (
                x["recipient__org_id_schema"].fillna("UKG")
            ),
            recipient_individual_primary_grant_reason_name=lambda x: (
                x["recipient_individual_primary_grant_reason"]
                .dropna()
                .map(Grant.GrantToIndividualsReason)
                .apply(lambda x: x.label)
            ),
            recipient_individual_secondary_grant_reason_name=lambda x: (
                x["recipient_individual_secondary_grant_reason"]
                .dropna()
                .map(Grant.GrantToIndividualsReason)
                .apply(lambda x: x.label)
            ),
            recipient_individual_grant_purpose=lambda x: (
                x["recipient_individual_grant_purpose"]
                .dropna()
                .apply(
                    lambda x: tuple(
                        Grant.GrantToIndividualsPurpose(y).value for y in json.loads(x)
                    )
                )
            ),
        )
        .assign(
            recipient_individual_grant_purpose_name=lambda x: (
                x["recipient_individual_grant_purpose"]
                .dropna()
                .apply(
                    lambda x: tuple(Grant.GrantToIndividualsPurpose(y).label for y in x)
                )
            ),
            category=lambda x: (
                x["funder__segment"].map(FUNDER_CATEGORIES).fillna("Unknown").apply(str)
            ),
            amount_awarded_GBP_band=lambda x: pd.cut(
                x["amount_awarded_GBP"],
                bins=AMOUNT_AWARDED_BINS,
                labels=AMOUNT_AWARDED_BINS_LABELS,
            ).cat.add_categories("Unknown"),
            annual_amount_band=lambda x: pd.cut(
                x["annual_amount"],
                bins=AMOUNT_AWARDED_BINS,
                labels=AMOUNT_AWARDED_BINS_LABELS,
            ).cat.add_categories("Unknown"),
            planned_dates_duration_band=lambda x: pd.cut(
                x["planned_dates_duration"],
                bins=DURATION_BINS,
                labels=DURATION_BINS_LABELS,
            ).cat.add_categories("Unknown"),
        )
        .rename(
            columns={
                "funder__segment": "segment",
                "recipient__org_id_schema": "org_id_schema",
            }
        )
    )

    recipient_finances = (
        pd.DataFrame(
            GrantRecipientYear.objects.filter(
                financial_year_end__gte=current_fy.start_date,
                financial_year_end__lte=current_fy.end_date,
            ).values(
                "recipient_id",
                "financial_year_end",
                "financial_year_start",
                "income",
                "spending",
                "employees",
            )
        )
        .groupby("recipient_id")
        .agg(
            **{
                "recipient_income": ("income", "sum"),
                "recipient_spending": ("spending", "sum"),
                "recipient_employees": ("employees", "sum"),
            }
        )
        .assign(
            recipient_income_band=lambda x: pd.cut(
                x["recipient_income"],
                bins=INCOME_BINS,
                labels=INCOME_BINS_LABELS,
            ).cat.add_categories("Unknown"),
        )
    )
    result = result.join(recipient_finances, on="recipient_id")

    return result


def grant_table(
    df: pd.DataFrame,
    columns: list[str] = DEFAULT_COLUMNS,
    n: int = 100,
    sortby: str = "-amount_awarded_GBP",
):
    sort_ascending = True
    if sortby.startswith("-"):
        sortby = sortby[1:]
        sort_ascending = False
    result = df.sort_values(sortby, ascending=sort_ascending)[DEFAULT_COLUMNS]
    if n:
        result = result[0:n]
    return result


def grant_summary(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
):
    summary = (
        df.groupby(groupby)
        .agg(**AGG_COLUMNS)
        .assign(
            **{
                "Grant amount": lambda x: (
                    x["Grant amount"].divide(1_000_000).astype(float)
                ),
                "Grant amount (Adjusted)": lambda x: (
                    x["Grant amount (Adjusted)"].divide(1_000_000).astype(float)
                ),
            }
        )
    )
    summary["% of grants"] = (
        summary["Grants"].divide(summary["Grants"].sum()).multiply(100).round(1)
    )
    summary["% of grant amount"] = (
        summary["Grant amount"]
        .divide(summary["Grant amount"].sum())
        .multiply(100)
        .round(1)
    )

    # do category totals
    if groupby == ["category", "segment"]:
        total_rows = (
            df.assign(segment="Total")
            .groupby(groupby)
            .agg(**AGG_COLUMNS)
            .assign(
                **{
                    "Grant amount": lambda x: (
                        x["Grant amount"].divide(1_000_000).astype(float)
                    ),
                    "Grant amount (Adjusted)": lambda x: (
                        x["Grant amount (Adjusted)"].divide(1_000_000).astype(float)
                    ),
                }
            )
        )
        for total_key, total_row in total_rows.iterrows():
            # skip certain keys
            if total_key not in SEGMENT_ORDER:
                continue
            summary.loc[total_key, :] = total_row

    total_row = (
        df.assign(**{k: "Total" for k in groupby})
        .groupby(groupby)
        .agg(**AGG_COLUMNS)
        .assign(
            **{
                "Grant amount": lambda x: (
                    x["Grant amount"].divide(1_000_000).astype(float)
                ),
                "Grant amount (Adjusted)": lambda x: (
                    x["Grant amount (Adjusted)"].divide(1_000_000).astype(float)
                ),
            }
        )
    )
    total_key = tuple("Total" for k in groupby)
    if len(total_key) == 1:
        total_key = total_key[0]
    summary.loc[total_key, :] = total_row.loc[total_key]

    summary = summary.rename(
        columns={
            "Grant amount": "Grant amount (£m)",
            "Grant amount (Adjusted)": "Grant amount (Adjusted) (£m)",
        }
    )
    if groupby == ["category", "segment"]:
        segment_order = []
        segments = summary.index.to_list()
        for segment_category in SEGMENT_ORDER:
            if segment_category in segments:
                segment_order.append(segment_category)
        segment_order.extend([x for x in segments if x not in segment_order])
        return summary.loc[segment_order, :]
    return summary


def grant_crosstab(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    column_field="amount_awarded_GBP_band",
    values_field="grant_id",
):
    aggfunc = "count" if values_field == "grant_id" else "sum"
    summary = (
        pd.crosstab(
            [df[f] for f in groupby],
            df[column_field].fillna("Unknown"),
            values=df[values_field],
            aggfunc=aggfunc,
        )
        .assign(
            Total=lambda x: x.sum(axis=1),
        )
        .mask(lambda x: x["Total"] == 0)
        .dropna(how="all")
    )

    # do category totals
    if groupby == ["category", "segment"]:
        total_rows = pd.crosstab(
            [df.assign(segment="Total")[f] for f in groupby],
            df[column_field].fillna("Unknown"),
            values=df[values_field],
            aggfunc=aggfunc,
        ).assign(
            Total=lambda x: x.sum(axis=1),
        )
        for total_key, total_row in total_rows.iterrows():
            # skip certain keys
            if total_key not in SEGMENT_ORDER:
                continue
            summary.loc[total_key, :] = total_row

    total_row = pd.crosstab(
        [df.assign(**{k: "Total" for k in groupby})[f] for f in groupby],
        df[column_field].fillna("Unknown"),
        values=df[values_field],
        aggfunc=aggfunc,
    ).assign(
        Total=lambda x: x.sum(axis=1),
    )
    total_key = tuple("Total" for k in groupby)
    if len(total_key) == 1:
        total_key = total_key[0]
    summary.loc[total_key, :] = total_row.loc[total_key]

    if values_field in ("amount_awarded_GBP", "annual_amount"):
        summary = summary.divide(1_000_000).astype(float).round(1)

    segment_order = []
    segments = summary.index.to_list()
    for segment_category in SEGMENT_ORDER:
        if segment_category in segments:
            segment_order.append(segment_category)
    segment_order.extend([x for x in segments if x not in segment_order])
    return summary.loc[segment_order, :]


def grant_by_size(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    return grant_crosstab(df, groupby, column_field="amount_awarded_GBP_band", **kwargs)


def grant_by_duration(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    return grant_crosstab(
        df, groupby, column_field="planned_dates_duration_band", **kwargs
    )


def recipient_types(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    return grant_crosstab(df, groupby, column_field="recipient_type", **kwargs)


def recipients_by_size(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    return grant_crosstab(df, groupby, column_field="recipient_income_band", **kwargs)


def recipients_by_scale(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    return grant_crosstab(df, groupby, column_field="recipient__scale", **kwargs)


def number_of_grants_by_recipient(df: pd.DataFrame):
    summary = (
        df.groupby("recipient_id")
        .agg(
            {
                "recipient_id": "count",
                "amount_awarded_GBP": "sum",
            }
        )
        .rename(
            columns={
                "recipient_id": "number_of_grants",
                "amount_awarded_GBP": "total_amount_awarded_GBP",
            }
        )
        .assign(
            **{
                "Number of grants received": lambda x: pd.cut(
                    x["number_of_grants"],
                    bins=[0, 1, 2, 3, 4, 5, 10, 20, 50, 100, float("inf")],
                    labels=[
                        "1",
                        "2",
                        "3",
                        "4",
                        "5",
                        "6-10",
                        "11-20",
                        "21-50",
                        "51-100",
                        "101+",
                    ],
                )
            }
        )["Number of grants received"]
        .value_counts()
        .rename("Number of recipients")
        .sort_index()
        .to_frame()
    )
    return summary


def who_funds_with_who(df: pd.DataFrame, groupby: str = "segment"):
    wfww = pd.crosstab(
        df["recipient_id"],
        df[groupby],
    )
    summary = []
    for value_1 in df[groupby].unique():
        for value_2 in df[groupby].unique():
            if value_1 == value_2:
                continue
            count = wfww[wfww[value_1].gt(0) & wfww[value_2].gt(0)].size
            if count > 0:
                summary.append(
                    (
                        value_1,
                        value_2,
                        count,
                    )
                )
    return pd.DataFrame(
        summary, columns=[f"{groupby} from", f"{groupby} to", "Number of recipients"]
    )
