from io import BytesIO

import numpy as np
import pandas as pd
from caradoc import DataOutput
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
)


def index(request):
    return render(request, "index.html.j2")


def funder_table(columns, **filters):
    return (
        pd.DataFrame.from_records(
            Funder.objects.filter(**filters)
            .order_by("-latest_grantmaking")[0:100]
            .values(
                "org_id",
                "name",
                "segment",
                "makes_grants_to_individuals",
                "latest_year__income",
                "latest_year__spending",
                "latest_year__spending_grant_making",
                "latest_year__spending_grant_making_individuals",
            )
        )
        .assign(
            makes_grants_to_individuals=(
                lambda x: x["makes_grants_to_individuals"].map({True: "✓", False: ""})
            ),
            latest_year__income=(
                lambda x: x["latest_year__income"].divide(1_000_000).round(1)
            ),
            latest_year__spending=(
                lambda x: x["latest_year__spending"].divide(1_000_000).round(1)
            ),
            latest_year__spending_grant_making=(
                lambda x: x["latest_year__spending_grant_making"]
                .divide(1_000_000)
                .round(1)
            ),
            latest_year__spending_grant_making_individuals=(
                lambda x: x["latest_year__spending_grant_making_individuals"]
                .divide(1_000_000)
                .round(1)
            ),
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
                "latest_year__income": "Income",
                "latest_year__spending": "Spending",
                "latest_year__spending_grant_making": "Grant Making Spending",
                "latest_year__spending_grant_making_individuals": "Grant Making Spending (Individuals)",
            }
        )
        .replace({np.nan: None, pd.NA: None})[columns]
    )


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
                    "Income",
                    "Spending",
                    "Grant Making Spending",
                ],
                segment=funder_type,
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
                "Income",
                "Spending",
                "Grant Making Spending",
                "Grant Making Spending (Individuals)",
            ],
            makes_grants_to_individuals=True,
        ),
        "Grants to individuals",
    )

    # table for tags
    for funder_tag in ["London Funders", "360Giving Publisher", "Living Wage Funder"]:
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
