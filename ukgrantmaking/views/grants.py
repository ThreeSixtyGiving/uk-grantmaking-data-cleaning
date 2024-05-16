from io import BytesIO

from caradoc import DataOutput, FinancialYear
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from ukgrantmaking.models.funder import (
    FUNDER_CATEGORIES,
    Funder,
    FunderCategory,
    FunderSegment,
)
from ukgrantmaking.utils.grant import (
    DEFAULT_COLUMNS,
    get_all_grants,
    grant_by_duration,
    grant_by_size,
    grant_summary,
    grant_table,
)


@login_required
def financial_year_grants_view(request, fy, filetype="html"):
    current_fy = FinancialYear(fy)
    output = DataOutput()

    all_grants = get_all_grants(current_fy)

    summaries = {
        "Grants to organisations": {
            "criteria": (all_grants["recipient_type"] != "Individual")
        },
        "Grants to organisations (excluding regrants)": {
            "criteria": (all_grants["recipient_type"] != "Individual")
            & all_grants["regrant_type"].isnull(),
        },
        "Grants to organisations (regrants)": {
            "criteria": (all_grants["recipient_type"] != "Individual")
            & all_grants["regrant_type"].notnull(),
        },
        "Grants to individuals": {
            "criteria": (all_grants["recipient_type"] == "Individual"),
        },
    }

    for summary_title, summary_filters in summaries.items():
        output.add_table(
            grant_summary(all_grants[summary_filters["criteria"]]),
            "Summary",
            title=summary_title,
        )
        output.add_table(
            grant_by_size(all_grants[summary_filters["criteria"]]),
            "Summary by size",
            title=summary_title,
        )
        output.add_table(
            grant_by_duration(all_grants[summary_filters["criteria"]]),
            "Summary by duration",
            title=summary_title,
        )

    output.add_table(
        grant_summary(
            all_grants[summaries["Grants to individuals"]["criteria"]],
            groupby=["funder_id", "funder_name", "segment"],
        ),
        "Individual grants",
        title="By funder",
    )
    for field in [
        "recipient_individual_primary_grant_reason",
        "recipient_individual_secondary_grant_reason",
        "recipient_individual_grant_purpose",
    ]:
        output.add_table(
            grant_summary(
                all_grants[summaries["Grants to individuals"]["criteria"]].explode(
                    [field, f"{field}_name"]
                ),
                groupby=[field, f"{field}_name"],
            )
            .reset_index()
            .rename(
                columns={
                    field: "Code",
                    f"{field}_name": "Name",
                }
            ),
            "Individual grants",
            title=(
                field.replace("recipient_individual_", "").replace("_", " ").title()
            ),
        )

    funders = (
        Funder.objects.filter(included=True)
        .exclude(segment=FunderSegment.CHARITY)
        .values_list("org_id", flat=True)
    )
    output.add_table(
        grant_table(
            all_grants[all_grants["recipient_id"].isin(funders)],
            n=None if filetype == "xlsx" else 100,
        ),
        "Regrants",
    )

    non_government_segments = [
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
    ]
    output.add_table(
        grant_table(
            all_grants[
                all_grants["org_id_schema"].isin(["UKG"])
                & all_grants["segment"].isin(non_government_segments)
            ],
            columns=DEFAULT_COLUMNS + (["description"] if filetype == "xlsx" else []),
            n=None if filetype == "xlsx" else 100,
        ),
        "Missing Org ID" if filetype == "html" else "Missing Org ID (Not government)",
        title="Grantmakers" if filetype == "html" else None,
    )

    output.add_table(
        grant_table(
            all_grants[
                all_grants["org_id_schema"].isin(["UKG"])
                & ~all_grants["segment"].isin(non_government_segments)
            ],
            columns=DEFAULT_COLUMNS + (["description"] if filetype == "xlsx" else []),
            n=None if filetype == "xlsx" else 100,
        ),
        "Missing Org ID" if filetype == "html" else "Missing Org ID (Government)",
        title="Government" if filetype == "html" else None,
    )

    output.add_table(
        grant_summary(
            all_grants[all_grants["segment"].isin(["Community Foundation"])],
            groupby=["funder_id", "funder_name"],
        ),
        "Community Foundations",
        title="Summary",
    )
    output.add_table(
        grant_by_size(
            all_grants[all_grants["segment"].isin(["Community Foundation"])],
            groupby=["funder_id", "funder_name"],
        ),
        "Community Foundations",
        title="Summary by size",
    )
    output.add_table(
        grant_by_duration(
            all_grants[all_grants["segment"].isin(["Community Foundation"])],
            groupby=["funder_id", "funder_name"],
        ),
        "Community Foundations",
        title="Summary by duration",
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
