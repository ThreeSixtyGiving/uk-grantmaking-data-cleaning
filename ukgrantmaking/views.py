from io import BytesIO

import numpy as np
import pandas as pd
from caradoc import DataOutput, FinancialYear
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models.lookups import GreaterThan
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import slugify

from ukgrantmaking.models import (
    FUNDER_CATEGORIES,
    Funder,
    FunderSegment,
    FunderTag,
)


@login_required
def index(request):
    return render(request, "index.html.j2")


def funder_table(current_fy, columns, n=100, sortby="-latest_grantmaking", **filters):
    agg_fields = [
        ("income", "Income"),
        ("spending", "Spending"),
        ("spending_grant_making", "Grant Making Spending"),
        ("spending_grant_making_institutions", "Grant Making Spending (Institutions)"),
        ("spending_grant_making_individuals", "Grant Making Spending (Individuals)"),
        ("total_net_assets", "Net Assets"),
        ("employees", "Employees"),
    ]
    tags = [
        ("Living Wage Funder", "Living Wage Funder"),
        ("360Giving Publisher", "360Giving Publisher"),
        ("ACO", "ACO Member"),
    ]
    annotations = {}
    assignments = {}
    for field, field_name in agg_fields:
        agg = models.Max if field in ("total_net_assets",) else models.Sum
        annotations[f"cy_{field}"] = agg(
            models.Case(
                models.When(
                    funderyear__financial_year=current_fy,
                    then=models.F(f"funderyear__{field}"),
                ),
                default=0,
                output_field=models.IntegerField(),
            )
        )
        annotations[f"py_{field}"] = agg(
            models.Case(
                models.When(
                    funderyear__financial_year=(current_fy - 1),
                    then=models.F(f"funderyear__{field}"),
                ),
                default=0,
                output_field=models.IntegerField(),
            )
        )

    funder_year_query = (
        Funder.objects.filter(**filters)
        .order_by(sortby)
        .values(
            "org_id",
            "name",
            "segment",
            "makes_grants_to_individuals",
        )
        .annotate(
            **annotations,
        )
    )

    tag_annotations = {}
    for tag, tag_name in tags:
        tag_annotations[slugify(tag).replace("-", "_")] = GreaterThan(
            models.Sum(
                models.Case(
                    models.When(tags__tag=tag, then=1),
                    default=0,
                    output_field=models.IntegerField(),
                )
            ),
            models.Value(0),
        )
        assignments[slugify(tag).replace("-", "_")] = (
            (lambda x: x["cy_income"].divide(1_000_000).round(1)),
        )

    funder_tag_query = (
        Funder.objects.filter(**filters)
        .order_by(sortby)
        .values(
            "org_id",
        )
        .annotate(
            **tag_annotations,
        )
    )

    df = (
        pd.DataFrame.from_records(funder_year_query[0:n])
        .join(
            pd.DataFrame.from_records(funder_tag_query).set_index("org_id"),
            on="org_id",
            how="left",
        )
        .assign(
            rank=lambda x: np.arange(x.shape[0]),
        )
        .assign(
            rank=lambda x: x["rank"] + 1,
        )
    )
    df["segment"] = (
        df["segment"].fillna("Unknown").replace({"Wellcome Trust": "Family Foundation"})
    )

    for tag, tag_name in tags + [
        ("makes_grants_to_individuals", "Makes grants to individuals")
    ]:
        tag_field = slugify(tag).replace("-", "_")
        df[tag_field] = df[tag_field].map({True: "✓", False: ""})

    for field, field_name in agg_fields:
        if field in ("employees",):
            df[f"cy_{field}"] = df[f"cy_{field}"].round(0)
            df[f"py_{field}"] = df[f"py_{field}"].round(0)
        else:
            df[f"cy_{field}"] = df[f"cy_{field}"].divide(1_000_000).round(1)
            df[f"py_{field}"] = df[f"py_{field}"].divide(1_000_000).round(1)

    return (
        df[columns]
        .rename(
            columns={
                "rank": "#",
                "org_id": "Org ID",
                "name": "Name",
                "segment": "Segment",
                "makes_grants_to_individuals": "Grants to Individuals",
                **{slugify(tag).replace("-", "_"): tag_name for tag, tag_name in tags},
                **{f"cy_{field}": field_name for field, field_name in agg_fields},
                **{
                    f"py_{field}": f"{field_name} (Previous year)"
                    for field, field_name in agg_fields
                },
            }
        )
        .replace({np.nan: None, pd.NA: None})
    )


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
                individuals=models.Sum("makes_grants_to_individuals"),
            )
        )
        .assign(
            segment=lambda x: x["segment"].fillna("Unknown"),
            category=lambda x: x["segment"].map(FUNDER_CATEGORIES).fillna("Unknown"),
            income=lambda x: x["income"].divide(1_000_000).round(1),
            spending=lambda x: x["spending"].divide(1_000_000).round(1),
            grantmaking=lambda x: x["grantmaking"].divide(1_000_000).round(1),
        )
        .rename(
            columns={
                "category": "Category",
                "segment": "Segment",
                "count": "Number of grantmakers",
                "income": "Total income",
                "spending": "Total spending",
                "grantmaking": "Spending on grants",
                "individuals": "Make grants to individuals",
            }
        )
        .set_index(["Category", "Segment"])
        .sort_index()
        .replace({False: pd.NA, np.nan: pd.NA, True: 1})
        .replace({pd.NA: None})
    )
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
                total=models.Count("segment"),
            )
        )
        .assign(
            segment=lambda x: x["segment"].fillna("Unknown"),
            category=lambda x: x["segment"].map(FUNDER_CATEGORIES).fillna("Unknown"),
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
    years = [str(fy) for fy in current_fy.previous_n_years(4)]
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
            trends_over_time, "Trends", title=f"Trend over time ({field_name})"
        )

    # table for each segment
    for funder_type in FUNDER_CATEGORIES.keys():
        funder_type_name = FunderSegment(funder_type).label
        output.add_table(
            funder_table(
                current_fy,
                [
                    "rank",
                    "org_id",
                    "name",
                    "makes_grants_to_individuals",
                    "living_wage_funder",
                    "360giving_publisher",
                    "cy_income",
                    "cy_spending",
                    "cy_spending_grant_making",
                    "cy_total_net_assets",
                ],
                segment=funder_type,
                included=True,
            ),
            slugify(funder_type_name) if filetype == "xlsx" else "Funder lists",
            title=funder_type_name if filetype != "xlsx" else None,
        )

    output.add_table(
        funder_table(
            current_fy,
            [
                "rank",
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
            ],
            makes_grants_to_individuals=True,
            included=True,
        ),
        "Grants to individuals",
    )

    output.add_table(
        funder_table(
            current_fy,
            [
                "rank",
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
                "py_spending_grant_making",
                "py_total_net_assets",
            ],
            n=300,
            included=True,
        ),
        "Top 300",
    )

    # table for tags
    for funder_tag in [
        "London Funders",
        "360Giving Publisher",
        "Living Wage Funder",
        "ACF Current",
        "ACO",
    ]:
        funder_tag_obj = FunderTag.objects.get(tag=funder_tag)
        output.add_table(
            funder_table(
                current_fy,
                [
                    "rank",
                    "org_id",
                    "name",
                    "segment",
                    "makes_grants_to_individuals",
                    "cy_income",
                    "cy_spending",
                    "cy_spending_grant_making",
                    "cy_total_net_assets",
                ],
                org_id__in=funder_tag_obj.funder_set.values_list("org_id", flat=True),
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
                "rank",
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
                "py_income",
                "py_spending",
                "py_spending_grant_making",
                "py_spending_grant_making_institutions",
                "py_spending_grant_making_individuals",
                "py_total_net_assets",
                "py_employees",
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
