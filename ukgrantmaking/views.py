from io import BytesIO

import numpy as np
import pandas as pd
from caradoc import DataOutput
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


def funder_table(columns, n=100, sortby="-latest_grantmaking", **filters):
    query = (
        Funder.objects.filter(**filters)
        .order_by(sortby)
        .values(
            "org_id",
            "name",
            "segment",
            "makes_grants_to_individuals",
            "latest_year__income",
            "latest_year__spending",
            "latest_year__spending_grant_making",
            "latest_year__spending_grant_making_institutions",
            "latest_year__spending_grant_making_individuals",
            "latest_year__total_net_assets",
            "latest_year__employees",
        )
        .annotate(
            living_wage_funder=GreaterThan(
                models.Sum(
                    models.Case(
                        models.When(tags__tag="Living Wage Funder", then=1),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                models.Value(0),
            ),
            tsg_publisher=GreaterThan(
                models.Sum(
                    models.Case(
                        models.When(tags__tag="360Giving Publisher", then=1),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                models.Value(0),
            ),
            aco_member=GreaterThan(
                models.Sum(
                    models.Case(
                        models.When(tags__tag="ACO", then=1),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                models.Value(0),
            ),
        )
    )

    return (
        pd.DataFrame.from_records(query[0:n])
        .assign(
            makes_grants_to_individuals=(
                lambda x: x["makes_grants_to_individuals"].map({True: "✓", False: ""})
            ),
            living_wage_funder=(
                lambda x: x["living_wage_funder"].map({True: "✓", False: ""})
            ),
            tsg_publisher=(lambda x: x["tsg_publisher"].map({True: "✓", False: ""})),
            aco_member=(lambda x: x["aco_member"].map({True: "✓", False: ""})),
            latest_year__income=(
                lambda x: x["latest_year__income"].divide(1_000_000).round(1)
            ),
            latest_year__spending=(
                lambda x: x["latest_year__spending"].divide(1_000_000).round(1)
            ),
            latest_year__spending_grant_making=lambda x: (
                x["latest_year__spending_grant_making"].divide(1_000_000).round(1)
            ),
            latest_year__spending_grant_making_institutions=lambda x: (
                x["latest_year__spending_grant_making_institutions"]
                .divide(1_000_000)
                .round(1)
            ),
            latest_year__spending_grant_making_individuals=lambda x: (
                x["latest_year__spending_grant_making_individuals"]
                .divide(1_000_000)
                .round(1)
            ),
            latest_year__total_net_assets=lambda x: (
                x["latest_year__total_net_assets"].divide(1_000_000).round(1)
            ),
            latest_year__employees=lambda x: (x["latest_year__employees"].round(0)),
            rank=lambda x: np.arange(x.shape[0]),
        )
        .assign(
            rank=lambda x: x["rank"] + 1,
        )
        .rename(
            columns={
                "rank": "#",
                "org_id": "Org ID",
                "name": "Name",
                "segment": "Segment",
                "makes_grants_to_individuals": "Grants to Individuals",
                "living_wage_funder": "Living Wage Funder",
                "tsg_publisher": "360Giving Publisher",
                "aco_member": "ACO Member",
                "latest_year__income": "Income",
                "latest_year__spending": "Spending",
                "latest_year__spending_grant_making": "Grant Making Spending",
                "latest_year__spending_grant_making_institutions": "Grant Making Spending (Institutions)",
                "latest_year__spending_grant_making_individuals": "Grant Making Spending (Individuals)",
                "latest_year__total_net_assets": "Net Assets",
                "latest_year__employees": "Employees",
            }
        )
        .replace({np.nan: None, pd.NA: None})[columns]
    )


@login_required
def financial_year(request, fy, filetype="html"):
    output = DataOutput()

    # summary table
    summary = (
        pd.DataFrame.from_records(
            Funder.objects.filter(
                included=True,
            )
            .values("segment")
            .annotate(
                count=models.Count("segment"),
                income=models.Sum("latest_year__income"),
                spending=models.Sum("latest_year__spending"),
                grantmaking=models.Sum("latest_year__spending_grant_making"),
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
                            models.Q(latest_year__spending=0)
                            | models.Q(latest_year__spending__isnull=True),
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                under_100k=models.Sum(
                    models.Case(
                        models.When(
                            latest_year__spending__lt=100_000,
                            latest_year__spending__gt=0,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _100k_1m=models.Sum(
                    models.Case(
                        models.When(
                            latest_year__spending__lt=1_000_000,
                            latest_year__spending__gte=100_000,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _1m_10m=models.Sum(
                    models.Case(
                        models.When(
                            latest_year__spending__lt=10_000_000,
                            latest_year__spending__gte=1_000_000,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                _10m_100m=models.Sum(
                    models.Case(
                        models.When(
                            latest_year__spending__lt=100_000_000,
                            latest_year__spending__gte=10_000_000,
                            then=1,
                        ),
                        default=0,
                        output_field=models.IntegerField(),
                    )
                ),
                over_100m=models.Sum(
                    models.Case(
                        models.When(
                            latest_year__spending__gte=100_000_000,
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
    fields = {
        "spending": "Spending",
        "income": "Income",
        "spending_grant_making": "Spending on grantmaking",
        "total_net_assets": "Net Assets",
    }
    years = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23"]
    for field, field_name in fields.items():
        year_annotations = {}
        for year in years:
            year_annotations[year] = models.Sum(
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
                [
                    "#",
                    "Org ID",
                    "Name",
                    "Grants to Individuals",
                    "Living Wage Funder",
                    "360Giving Publisher",
                    "Income",
                    "Spending",
                    "Grant Making Spending",
                    "Net Assets",
                ],
                segment=funder_type,
                included=True,
            ),
            slugify(funder_type_name) if filetype == "xlsx" else "Funder lists",
            title=funder_type_name if filetype != "xlsx" else None,
        )

    output.add_table(
        funder_table(
            [
                "#",
                "Org ID",
                "Name",
                "Segment",
                "Living Wage Funder",
                "360Giving Publisher",
                "ACO Member",
                "Income",
                "Spending",
                "Grant Making Spending",
                "Grant Making Spending (Individuals)",
                "Net Assets",
            ],
            makes_grants_to_individuals=True,
            included=True,
        ),
        "Grants to individuals",
    )

    output.add_table(
        funder_table(
            [
                "#",
                "Org ID",
                "Name",
                "Segment",
                "Living Wage Funder",
                "360Giving Publisher",
                "ACO Member",
                "Income",
                "Spending",
                "Grant Making Spending",
                "Grant Making Spending (Individuals)",
                "Net Assets",
                "Employees",
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
                [
                    "#",
                    "Org ID",
                    "Name",
                    "Segment",
                    "Grants to Individuals",
                    "Income",
                    "Spending",
                    "Grant Making Spending",
                    "Net Assets",
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
