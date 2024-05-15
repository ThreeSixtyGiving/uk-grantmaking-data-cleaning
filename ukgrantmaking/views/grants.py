from io import BytesIO

import pandas as pd
from caradoc import DataOutput, FinancialYear
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from ukgrantmaking.models.funder import (
    FUNDER_CATEGORIES,
    Funder,
    FunderCategory,
    FunderSegment,
)
from ukgrantmaking.models.grant import Grant
from ukgrantmaking.utils.grant import grant_by_size, grant_summary, grant_table


@login_required
def financial_year_grants_view(request, fy, filetype="html"):
    current_fy = FinancialYear(fy)
    output = DataOutput()

    summaries = {
        "Grants to organisations": {
            "recipient_type": Grant.RecipientType.ORGANISATION,
        },
        "Grants to organisations (excluding regrants)": {
            "recipient_type": Grant.RecipientType.ORGANISATION,
            "regrant_type__isnull": True,
        },
        "Grants to individuals": {
            "recipient_type": Grant.RecipientType.INDIVIDUAL,
        },
    }

    for summary_title, summary_filters in summaries.items():
        output.add_table(
            grant_summary(
                current_fy=current_fy,
                inclusion__in=[
                    Grant.InclusionStatus.INCLUDED,
                    Grant.InclusionStatus.UNSURE,
                ],
                **summary_filters,
            ),
            "Summary",
            title=summary_title,
        )
        output.add_table(
            grant_by_size(
                current_fy=current_fy,
                inclusion__in=[
                    Grant.InclusionStatus.INCLUDED,
                    Grant.InclusionStatus.UNSURE,
                ],
                **summary_filters,
            ),
            "Summary by size",
            title=summary_title,
        )

    funders = (
        Funder.objects.filter(included=True)
        .exclude(segment=FunderSegment.CHARITY)
        .values_list("org_id", flat=True)
    )
    output.add_table(
        grant_table(
            current_fy=current_fy,
            n=None if filetype == "xlsx" else 100,
            recipient_organisation_id__in=funders,
        ),
        "Regrants",
    )

    output.add_table(
        grant_table(
            current_fy=current_fy,
            n=None if filetype == "xlsx" else 100,
            recipient__org_id_schema="UKG",
            inclusion__in=[
                Grant.InclusionStatus.INCLUDED,
                Grant.InclusionStatus.UNSURE,
            ],
            funder__segment__in=[
                k
                for k, v in FUNDER_CATEGORIES.items()
                if (
                    v
                    in [
                        FunderCategory.GRANTMAKER,
                        FunderCategory.OTHER,
                        FunderCategory.CHARITY,
                    ]
                )
                and (k != FunderSegment.WELLCOME_TRUST)
            ],
        ),
        "Missing Org ID" if filetype == "html" else "Missing Org ID (Not government)",
        title="Grantmakers" if filetype == "html" else None,
    )

    output.add_table(
        grant_table(
            current_fy=current_fy,
            n=None if filetype == "xlsx" else 100,
            recipient__org_id_schema="UKG",
            inclusion__in=[
                Grant.InclusionStatus.INCLUDED,
                Grant.InclusionStatus.UNSURE,
            ],
            funder__segment__in=[
                k
                for k, v in FUNDER_CATEGORIES.items()
                if v
                not in [
                    FunderCategory.GRANTMAKER,
                    FunderCategory.OTHER,
                    FunderCategory.CHARITY,
                ]
            ],
        ),
        "Missing Org ID" if filetype == "html" else "Missing Org ID (Government)",
        title="Government" if filetype == "html" else None,
    )

    if filetype == "xlsx":
        buffer = BytesIO()
        output.write(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f"attachment; filename=grants-{fy}.xlsx"
        return response

    return render(
        request,
        "financial_year.html.j2",
        {
            "fy": fy,
            "output": output,
            "skip_sheets": ["All general grantmakers"],
            "xlsx_link": reverse("financial_year_grants_xlsx", kwargs={"fy": fy}),
        },
    )
