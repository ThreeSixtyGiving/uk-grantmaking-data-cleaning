from io import BytesIO
from typing import Optional

import numpy as np
import pandas as pd
from caradoc import DataOutput, FinancialYear
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import slugify

from ukgrantmaking.models import (
    FUNDER_CATEGORIES,
    Funder,
    FunderSegment,
    FunderTag,
    FunderYear,
)


@login_required
def index(request):
    return render(request, "index.html.j2")


def funder_table(
    current_fy: FinancialYear,
    columns: list[str],
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
            cy_income=("income", "sum"),
            cy_spending=("spending", "sum"),
            cy_spending_grant_making=("spending_grant_making", "sum"),
            cy_spending_grant_making_institutions=(
                "spending_grant_making_institutions",
                "sum",
            ),
            cy_spending_grant_making_individuals=(
                "spending_grant_making_individuals",
                "sum",
            ),
            cy_total_net_assets=("total_net_assets", "max"),
            cy_funds_endowment=("funds_endowment", "max"),
            cy_employees=("employees", "max"),
            cy_scale=("scale", "sum"),
            cy_notes=("notes", "first"),
        ),
        on="org_id",
        how="left",
    ).join(
        py_data.groupby("funder_id").agg(
            py_income=("income", "sum"),
            py_spending=("spending", "sum"),
            py_spending_grant_making=("spending_grant_making", "sum"),
            py_spending_grant_making_institutions=(
                "spending_grant_making_institutions",
                "sum",
            ),
            py_spending_grant_making_individuals=(
                "spending_grant_making_individuals",
                "sum",
            ),
            py_total_net_assets=("total_net_assets", "max"),
            py_funds_endowment=("funds_endowment", "max"),
            py_employees=("employees", "max"),
            py_scale=("scale", "sum"),
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
        df = df[df["cy_spending"] >= spending_threshold]

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
            }
        )
        .replace({np.nan: None, pd.NA: None})
    )


def funders_over_time(
    current_fy: FinancialYear,
    columns: list[tuple[str, str, models.Aggregate]],
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
        .values("org_id", "name")
        .annotate(**year_annotations)
    )
    trends_over_time = (
        pd.DataFrame.from_records(trends_query)
        .rename(
            columns={
                "org_id": "Org ID",
                "name": "Funder name",
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


@login_required
def financial_year(request, fy, filetype="html"):
    current_fy = FinancialYear(fy)

    output = DataOutput()

    # summary table
    summary = (
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
    summary.loc[("Total", "Total"), :] = summary.sum(axis=0)
    output.add_table(summary, "Summary", title="Summary")

    # summary by size
    summary_by_size = (
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
                                funderyear__spending=0,
                                funderyear__financial_year=current_fy,
                            )
                            | models.Q(
                                funderyear__spending__isnull=True,
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
                            funderyear__spending__lt=100_000,
                            funderyear__spending__gt=0,
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
                            funderyear__spending__lt=1_000_000,
                            funderyear__spending__gte=100_000,
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
                            funderyear__spending__lt=10_000_000,
                            funderyear__spending__gte=1_000_000,
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
                            funderyear__spending__lt=100_000_000,
                            funderyear__spending__gte=10_000_000,
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
                            funderyear__spending__gte=100_000_000,
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
    output.add_table(summary_by_size, "Summary", title="Grantmakers by grant spending")

    # trends over time
    fields = [
        ("spending", "Spending", models.Sum),
        ("income", "Income", models.Sum),
        ("spending_grant_making", "Spending on grantmaking", models.Sum),
        ("total_net_assets", "Net Assets", models.Max),
    ]
    years = [str(fy) for fy in current_fy.previous_n_years(4)][::-1]
    for field, field_name, aggregation in fields:
        year_annotations = {}
        for year in years:
            year_annotations[year] = aggregation(
                models.Case(
                    models.When(
                        funderyear__financial_year=year,
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
                category=(
                    lambda x: x["segment"].map(FUNDER_CATEGORIES).fillna("Unknown")
                ),
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
            trends_over_time[f"{year} Count"] = trends_over_time[
                f"{year}_count"
            ].astype("int")
            del trends_over_time[f"{year}_count"]
        output.add_table(
            trends_over_time,
            "Trends",
            title=f"Trend over time ({field_name})",
        )

    # trends by segment
    trend_segments = [
        ("Family Foundation", 100),
        ("Corporate Foundation", 50),
        ("General grantmaker", 100),
    ]
    for segment, segment_n in trend_segments:
        segment_trends_over_time = funders_over_time(
            current_fy,
            [
                ("spending_grant_making", "Spending on grantmaking", models.Sum),
                ("total_net_assets", "Net Assets", models.Max),
            ],
            n=segment_n,
            included=True,
            segment=segment,
        )
        output.add_table(
            segment_trends_over_time,
            f"trends-{slugify(segment)}"
            if filetype == "xlsx"
            else "Trends (by segment)",
            title=f"Trend over time ({segment})" if filetype != "xlsx" else None,
        )

    endowment_trends_over_time = funders_over_time(
        current_fy,
        [
            ("funds_endowment", "Endowment Funds", models.Max),
        ],
        n=100,
        sortby="-cy_funds_endowment",
        included=True,
    )
    output.add_table(
        endowment_trends_over_time,
        "trends-endowments" if filetype == "xlsx" else "Trends (by segment)",
        title="Trend over time (Endowments)" if filetype != "xlsx" else None,
    )

    # table for each segment
    for segment in FUNDER_CATEGORIES.keys():
        if segment == FunderSegment.SMALL_GRANTMAKER:
            continue
        segment_name = FunderSegment(segment).label
        n = 100
        if segment == FunderSegment.FAMILY_FOUNDATION:
            n = 150
        output.add_table(
            funder_table(
                current_fy,
                [
                    "cy_rank",
                    "org_id",
                    "name",
                    "makes_grants_to_individuals",
                    "living_wage_funder",
                    "360giving_publisher",
                    "cy_income",
                    "cy_spending",
                    "cy_spending_grant_making",
                    "cy_spending_grant_making_individuals",
                    "cy_total_net_assets",
                    "cy_employees",
                    "py_rank",
                    "py_income",
                    "py_spending",
                    "py_spending_grant_making",
                    "py_spending_grant_making_individuals",
                    "py_total_net_assets",
                    "py_employees",
                    "notes",
                ],
                n=n,
                segment=segment,
                included=True,
            ),
            slugify(segment_name) if filetype == "xlsx" else "Funder lists",
            title=segment_name if filetype != "xlsx" else None,
        )

    # all general grantmakers
    output.add_table(
        funder_table(
            current_fy,
            [
                "cy_rank",
                "org_id",
                "name",
                "makes_grants_to_individuals",
                "living_wage_funder",
                "360giving_publisher",
                "cy_income",
                "cy_spending",
                "cy_spending_grant_making",
                "cy_spending_grant_making_individuals",
                "cy_total_net_assets",
                "cy_employees",
                "py_rank",
                "py_income",
                "py_spending",
                "py_spending_grant_making",
                "py_spending_grant_making_individuals",
                "py_total_net_assets",
                "py_employees",
                "notes",
            ],
            segment=FunderSegment.GENERAL_GRANTMAKER,
            included=True,
            n=1_000_000,
        ),
        "All general grantmakers",
        title="All general grantmakers",
    )

    output.add_table(
        funder_table(
            current_fy,
            [
                "cy_rank",
                "org_id",
                "name",
                "segment",
                "living_wage_funder",
                "360giving_publisher",
                "aco",
                "cy_income",
                "cy_spending",
                "cy_spending_grant_making",
                "cy_spending_grant_making_individuals",
                "cy_total_net_assets",
                "py_income",
                "py_spending",
                "py_spending_grant_making",
                "py_spending_grant_making_individuals",
                "py_total_net_assets",
                "notes",
            ],
            sortby="-cy_spending_grant_making_individuals",
            makes_grants_to_individuals=True,
            included=True,
        ),
        "Grants to individuals",
    )

    output.add_table(
        funder_table(
            current_fy,
            [
                "cy_rank",
                "org_id",
                "name",
                "segment",
                "living_wage_funder",
                "360giving_publisher",
                "aco",
                "makes_grants_to_individuals",
                "cy_income",
                "cy_spending",
                "cy_spending_grant_making",
                "cy_spending_grant_making_individuals",
                "cy_total_net_assets",
                "cy_employees",
                "py_rank",
                "py_spending_grant_making",
                "py_total_net_assets",
                "notes",
            ],
            n=300,
            included=True,
        ),
        "Top 300",
    )

    # table for tags
    for funder_tag in [
        "London Funders",
        "London Local Giving Scheme",
        "360Giving Publisher",
        "Living Wage Funder",
        "ACF Current",
        "ACO",
        "Companies & Guilds",
        "Funders Forum for NI",
        "OSCR",
        "CCNI",
    ]:
        funder_tag_obj = FunderTag.objects.get(tag=funder_tag)
        output.add_table(
            funder_table(
                current_fy,
                [
                    "cy_rank",
                    "org_id",
                    "name",
                    "segment",
                    "makes_grants_to_individuals",
                    "360giving_publisher",
                    "cy_income",
                    "cy_spending",
                    "cy_spending_grant_making",
                    "cy_spending_grant_making_individuals",
                    "cy_total_net_assets",
                    "notes",
                ],
                tag_children=[funder_tag_obj.tag],
                org_id__in=funder_tag_obj.funders.values_list("org_id", flat=True),
                included=True,
                spending_threshold=None,
                n=1_000_000,
            ),
            slugify(funder_tag) if filetype == "xlsx" else "Funder tag lists",
            title=funder_tag if filetype != "xlsx" else None,
        )

    if filetype == "xlsx":
        buffer = BytesIO()
        output.write(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f"attachment; filename=grantmakers-{fy}.xlsx"
        return response

    return render(
        request,
        "financial_year.html.j2",
        {
            "fy": fy,
            "output": output,
            "skip_sheets": ["All general grantmakers"],
            "xlsx_link": reverse("financial_year_xlsx", kwargs={"fy": fy}),
        },
    )


@login_required
def all_grantmakers_export(request, fy, filetype):
    current_fy = FinancialYear(fy)
    output = DataOutput()
    output.add_table(
        funder_table(
            current_fy,
            [
                "cy_rank",
                "org_id",
                "name",
                "segment",
                "living_wage_funder",
                "360giving_publisher",
                "aco",
                "makes_grants_to_individuals",
                "cy_income",
                "cy_spending",
                "cy_spending_grant_making",
                "cy_spending_grant_making_institutions",
                "cy_spending_grant_making_individuals",
                "cy_total_net_assets",
                "cy_employees",
                "cy_notes",
                "py_income",
                "py_spending",
                "py_spending_grant_making",
                "py_spending_grant_making_institutions",
                "py_spending_grant_making_individuals",
                "py_total_net_assets",
                "py_employees",
                "py_notes",
            ],
            n=100_000,
        ),
        "All funders",
    )
    if filetype == "xlsx":
        buffer = BytesIO()
        output.write(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            f"attachment; filename=grantmakers-all.{filetype}"
        )
        return response

    raise ValueError(f"Unknown filetype: {filetype}")
