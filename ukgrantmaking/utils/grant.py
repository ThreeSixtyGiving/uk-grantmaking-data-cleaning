import json

import pandas as pd
from caradoc import FinancialYear
from django.db import models

from ukgrantmaking.models.grant import Grant, GrantRecipientYear

DEFAULT_COLUMNS = [
    # "grant_id",
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
    ("National Lottery", "National Lottery Distributor"),
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
    1_000,
    10_000,
    100_000,
    1_000_000,
    float("inf"),
]
AMOUNT_AWARDED_BINS_LABELS = [
    "Under £1k",
    "£1k to £10k",
    "£10k to £100k",
    "£100k to £1m",
    "Over £1m",
]
INCOME_BINS = [
    float("-inf"),
    10_000,
    100_000,
    1_000_000,
    10_000_000,
    float("inf"),
]
INCOME_BINS_LABELS = [
    "Under £10k",
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
    "13 months - 2 years",
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

GEO_LOOKUPS = {
    "E12000001": "North East",
    "E12000002": "North West",
    "E12000003": "Yorkshire and The Humber",
    "E12000004": "East Midlands",
    "E12000005": "West Midlands",
    "E12000006": "East of England",
    "E12000007": "London",
    "E12000008": "South East",
    "E12000009": "South West",
    "E92000001": "England",
    "K02000001": "United Kingdom",
    "K03000001": "Great Britain",
    "K04000001": "England and Wales",
    "L93000001": "Channel Islands",
    "M83000003": "Isle of Man",
    "N92000002": "Northern Ireland",
    "S92000003": "Scotland",
    "W92000004": "Wales",
    "E99999999": "England",
    "N99999999": "Northern Ireland",
    "S99999999": "Scotland",
    "W99999999": "Wales",
}


def get_all_grants(current_fy: FinancialYear):
    columns = [
        "grant_id",
        "funding_organisation_id",
        "funding_organisation_name",
        "recipient_organisation_id",
        "recipient_organisation_name",
        "title",
        "description",
        "amount_awarded_GBP",
        "annual_amount",
        "planned_dates_duration",
        "award_date",
        "regrant_type",
        "inclusion",
        "funder__segment",
        "funder__category",
        "recipient__org_id_schema",
        "recipient__how",
        "recipient__what",
        "recipient__who",
        "recipient__scale",
        "recipient_individual_primary_grant_reason",
        "recipient_individual_secondary_grant_reason",
        "recipient_individual_grant_purpose",
        "recipient_location_rgn",
        "recipient_location_ctry",
        "beneficiary_location_rgn",
        "beneficiary_location_ctry",
        "recipient__rgn_hq",
        "recipient__rgn_aoo",
        "recipient__ctry_hq",
        "recipient__ctry_aoo",
        "recipient__london_hq",
        "recipient__london_aoo",
        "recipient_type",
    ]
    result = (
        pd.DataFrame(
            Grant.objects.filter(
                award_date__gte=current_fy.start_date,
                award_date__lte=current_fy.end_date,
                amount_awarded_GBP__gte=0,
                inclusion__in=[
                    Grant.InclusionStatus.INCLUDED,
                    Grant.InclusionStatus.UNSURE,
                ],
            )
            .values(*columns)
            .annotate(
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
            category=lambda x: x["funder__category"].fillna("Unknown"),
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
            country=lambda x: (
                x["beneficiary_location_ctry"]
                .fillna(x["recipient_location_ctry"])
                .fillna(x["recipient__ctry_hq"])
                .map(GEO_LOOKUPS)
            ),
            region=lambda x: (
                x["beneficiary_location_rgn"]
                .fillna(x["recipient_location_rgn"])
                .fillna(x["recipient__rgn_hq"])
                .fillna(x["country"])
                .map(GEO_LOOKUPS)
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
            recipient_type=lambda x: (
                x["recipient_type"]
                .fillna("Unknown")
                .map(
                    {
                        "Charity": "Charity",
                        "Community Interest Company": "Other non-profit",
                        "Education": "University/Education",
                        "Local Authority": "Government",
                        "Mutual": "Other non-profit",
                        "NHS": "Government",
                        "Non-profit Company": "Other non-profit",
                        "Organisation": "Unknown",
                        "Individual": "Individual",
                        "Unknown": "Unknown",
                        "Overseas Charity": "Charity",
                        "Private Company": "Private Company",
                        "Sports Club": "Other non-profit",
                        "University": "University/Education",
                    }
                )
            ),
        )
        .rename(
            columns={
                "funder__segment": "segment",
                "recipient__org_id_schema": "org_id_schema",
            }
        )
    )

    # Add london category
    result["london_category"] = (
        result["recipient__scale"]
        .replace(
            {
                "Local": "London",
                "Regional": "London",
            }
        )
        .fillna(pd.NA)
    )
    result.loc[result["recipient__london_aoo"].fillna(False), "london_category"] = (
        "London"
    )
    result.loc[~result["recipient__london_hq"].fillna(False), "london_category"] = pd.NA

    # fix for minimum durations
    result.loc[result["planned_dates_duration"].lt(0), "planned_dates_duration"] = None

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
    result = df.set_index("grant_id").sort_values(sortby, ascending=sort_ascending)[
        columns
    ]
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
    return summary.loc[segment_order, :].fillna(0)


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


def grants_by_region(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    return grant_crosstab(df, groupby, column_field="region", **kwargs)


def grants_by_country(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    return grant_crosstab(df, groupby, column_field="country", **kwargs)


def explode_crosstab(df: pd.DataFrame, groupby: list[str], field: str, **kwargs):
    ct = grant_crosstab(
        df[df[field].notnull()].explode(field).reset_index(),
        groupby,
        column_field=field,
        **kwargs,
    )
    ct_total = grant_crosstab(
        df[df[field].notnull()].assign(**{field: "Blah"}),
        groupby,
        column_field=field,
        **kwargs,
    )
    ct.loc[:, "Total"] = ct_total.loc[:, "Total"]
    return ct


def grants_by_who(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    field = "recipient__who"
    return explode_crosstab(
        df,
        groupby,
        field,
        **kwargs,
    )


def grants_by_how(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    field = "recipient__how"
    return explode_crosstab(
        df,
        groupby,
        field,
        **kwargs,
    )


def grants_by_what(
    df: pd.DataFrame,
    groupby: list[str] = ["category", "segment"],
    **kwargs,
):
    field = "recipient__what"
    return explode_crosstab(
        df,
        groupby,
        field,
        **kwargs,
    )


def recipient_size_by_amount_awarded(df: pd.DataFrame, **kwargs):
    return grant_crosstab(
        df,
        ["amount_awarded_GBP_band"],
        column_field="recipient_income_band",
        **kwargs,
    )


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
            count = wfww[wfww[value_1].gt(0) & wfww[value_2].gt(0)].shape[0]
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
