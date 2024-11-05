from datetime import date, datetime, timezone
from io import BytesIO

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
    FunderCategory,
    FunderSegment,
    FunderTag,
)
from ukgrantmaking.utils.funder import (
    funder_individuals_summary,
    funder_over_time,
    funder_summary,
    funder_summary_by_size,
    funder_table,
    funder_trend_over_time,
)


@login_required
def grantmakers_trends(request, fy, filetype="html"):
    current_fy = FinancialYear(fy)
    effective_date = request.GET.get("effective_date", date.today().isoformat())
    effective_date = datetime.combine(
        date.fromisoformat(effective_date), datetime.max.time(), tzinfo=timezone.utc
    )

    output = DataOutput()

    # trends over time
    fields = [
        ("spending", "Spending", models.Sum),
        ("income", "Income", models.Sum),
        ("spending_grant_making", "Spending on grantmaking", models.Sum),
        ("total_net_assets", "Net Assets", models.Max),
        ("funds_endowment", "Endowments", models.Max),
    ]
    years = [str(fy) for fy in current_fy.previous_n_years(4)][::-1]
    for field, field_name, aggregation in fields:
        trends_over_time = funder_trend_over_time(
            years, field, aggregation, effective_date=effective_date
        )
        output.add_table(
            trends_over_time,
            "Trends",
            title=f"Trend over time ({field_name})",
        )

        funder_trend = funder_over_time(
            current_fy,
            [
                (field, field_name, aggregation),
            ],
            effective_date=effective_date,
            n=1_500 if filetype == "xlsx" else 150,
            included=True,
            sortby=f"-cy_{field}",
        )
        output.add_table(
            funder_trend,
            f"trends-funders-{field}"[0:31] if filetype == "xlsx" else "Trends",
            title=f"Trend over time (top funders by {field_name})",
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
            f"attachment; filename=grantmakers-trends-{fy}.xlsx"
        )
        return response

    query = ""
    if "effective_date" in request.GET:
        query = f"?effective_date={request.GET['effective_date']}"

    return render(
        request,
        "financial_year.html.j2",
        {
            "fy": fy,
            "output": output,
            "skip_sheets": ["All general grantmakers"],
            "links": {
                "Download as XLSX": reverse(
                    "grantmakers_trends_xlsx", kwargs={"fy": fy}
                )
                + query,
                "Download all funders as CSV": reverse(
                    "all_grantmakers_csv", kwargs={"fy": fy}
                ),
                "Grantmakers data": reverse("financial_year", kwargs={"fy": fy})
                + query,
            },
        },
    )


@login_required
def financial_year(request, fy, filetype="html"):
    current_fy = FinancialYear(fy)
    effective_date = request.GET.get("effective_date", date.today().isoformat())
    effective_date = datetime.combine(
        date.fromisoformat(effective_date), datetime.max.time(), tzinfo=timezone.utc
    )

    output = DataOutput()

    # summary table
    summary = funder_summary(current_fy, effective_date=effective_date)
    output.add_table(summary, "Summary", title="Summary")

    # summary by size
    summary_by_size = funder_summary_by_size(current_fy, effective_date=effective_date)
    output.add_table(summary_by_size, "Summary", title="Grantmakers by grant spending")

    # summary table grants to individuals
    summary_individuals = funder_individuals_summary(
        current_fy, effective_date=effective_date
    )
    output.add_table(
        summary_individuals, "Summary", title="Summary grants to individuals"
    )

    # summary table
    summary = funder_summary(current_fy - 1, effective_date=effective_date)
    output.add_table(summary, "Summary", title="Summary (previous year)")

    # summary by size
    summary_by_size = funder_summary_by_size(
        current_fy - 1, effective_date=effective_date
    )
    output.add_table(
        summary_by_size,
        "Summary",
        title="Grantmakers by grant spending (previous year)",
    )

    # summary table grants to individuals
    summary_individuals = funder_individuals_summary(
        current_fy - 1, effective_date=effective_date
    )
    output.add_table(
        summary_individuals,
        "Summary",
        title="Summary grants to individuals (previous year)",
    )

    # # trends over time
    # fields = [
    #     ("spending", "Spending", models.Sum),
    #     ("income", "Income", models.Sum),
    #     ("spending_grant_making", "Spending on grantmaking", models.Sum),
    #     ("total_net_assets", "Net Assets", models.Max),
    #     ("funds_endowment", "Endowments", models.Max),
    # ]
    # years = [str(fy) for fy in current_fy.previous_n_years(4)][::-1]
    # for field, field_name, aggregation in fields:
    #     trends_over_time = funder_trend_over_time(years, field, aggregation)
    #     output.add_table(
    #         trends_over_time,
    #         "Trends",
    #         title=f"Trend over time ({field_name})",
    #     )

    #     funder_trend = funder_over_time(
    #         current_fy,
    #         [
    #             (field, field_name, aggregation),
    #         ],
    #         n=1_500 if filetype == "xlsx" else 150,
    #         included=True,
    #         sortby=f"-cy_{field}",
    #     )
    #     output.add_table(
    #         funder_trend,
    #         f"trends-funders-{field}" if filetype == "xlsx" else "Trends",
    #         title=f"Trend over time (top funders by {field_name})",
    #     )

    # trends by segment
    trend_segments = [
        ("Family Foundation", 100),
        ("Corporate Foundation", 50),
        ("General grantmaker", 100),
    ]
    for segment, segment_n in trend_segments:
        segment_trends_over_time = funder_over_time(
            current_fy,
            [
                ("spending_grant_making", "Spending on grantmaking", models.Sum),
                ("total_net_assets", "Net Assets", models.Max),
            ],
            effective_date=effective_date,
            n=segment_n,
            included=True,
            segment=segment,
        )
        output.add_table(
            segment_trends_over_time,
            f"trends-{slugify(segment)}"[0:30]
            if filetype == "xlsx"
            else "Trends (by segment)",
            title=f"Trend over time ({segment})" if filetype != "xlsx" else None,
        )

    endowment_trends_over_time = funder_over_time(
        current_fy,
        [
            ("funds_endowment", "Endowment Funds", models.Max),
        ],
        effective_date=effective_date,
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
                    "cy_fye",
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
                effective_date=effective_date,
                n=n,
                segment=segment,
                included=True,
                spending_threshold=None,
            ),
            slugify(segment_name)[0:30] if filetype == "xlsx" else "Funder lists",
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
                "cy_fye",
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
            effective_date=effective_date,
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
                "cy_fye",
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
            effective_date=effective_date,
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
                "cy_fye",
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
            effective_date=effective_date,
            n=300,
            included=True,
            segment__in=[
                segment
                for segment, category in FUNDER_CATEGORIES.items()
                if category in [FunderCategory.GRANTMAKER]
            ],
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
        "Companies & Guilds",
        "Funders Forum for NI",
        "OSCR",
        "CCNI",
        "Sainsburys Family Charitable Trusts",
        "Postcode Lottery",
    ]:
        try:
            funder_tag_obj = FunderTag.objects.get(tag=funder_tag)
        except FunderTag.DoesNotExist:
            continue
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
                    "cy_fye",
                    "cy_income",
                    "cy_spending",
                    "cy_spending_grant_making",
                    "cy_spending_grant_making_individuals",
                    "cy_total_net_assets",
                    "cy_employees",
                    "py_income",
                    "py_spending",
                    "py_spending_grant_making",
                    "py_spending_grant_making_individuals",
                    "py_total_net_assets",
                    "py_employees",
                    "notes",
                ],
                effective_date=effective_date,
                tag_children=[funder_tag_obj.tag],
                org_id__in=funder_tag_obj.funders.values_list("org_id", flat=True),
                included=True,
                spending_threshold=None,
                n=1_000_000,
            ),
            slugify(funder_tag)[0:30] if filetype == "xlsx" else "Funder tag lists",
            title=funder_tag if filetype != "xlsx" else None,
        )

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
                "date_of_registration",
                "cy_fye",
                "cy_income",
                "cy_spending",
                "cy_spending_grant_making",
                "cy_spending_grant_making_individuals",
                "cy_total_net_assets",
                "notes",
            ],
            effective_date=effective_date,
            date_of_registration__gte=current_fy.start_date - pd.DateOffset(years=1),
            included=True,
            spending_threshold=None,
            n=1_000_000,
        ),
        "New funders",
        title="New funders" if filetype != "xlsx" else None,
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

    query = ""
    if "effective_date" in request.GET:
        query = f"?effective_date={request.GET['effective_date']}"

    return render(
        request,
        "financial_year.html.j2",
        {
            "fy": fy,
            "output": output,
            "skip_sheets": ["All general grantmakers"],
            "links": {
                "Download as XLSX": reverse("financial_year_xlsx", kwargs={"fy": fy})
                + query,
                "Download all funders as CSV": reverse(
                    "all_grantmakers_csv", kwargs={"fy": fy}
                ),
                "Grantmakers trends data": reverse(
                    "grantmakers_trends", kwargs={"fy": fy}
                )
                + query,
            },
        },
    )


@login_required
def all_grantmakers_csv(request, fy):
    current_fy = FinancialYear(fy)
    all_funders = funder_table(
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
            "cy_fye",
            "cy_income",
            "cy_spending",
            "cy_spending_grant_making",
            "cy_spending_grant_making_institutions",
            "cy_spending_grant_making_individuals",
            "cy_total_net_assets",
            "cy_funds_endowment",
            "cy_employees",
            "cy_notes",
            "py_fye",
            "py_income",
            "py_spending",
            "py_spending_grant_making",
            "py_spending_grant_making_institutions",
            "py_spending_grant_making_individuals",
            "py_total_net_assets",
            "py_funds_endowment",
            "py_employees",
            "py_notes",
        ],
        n=None,
        included=True,
    )

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="all-grantmakers-{current_fy}.csv"'
        },
    )
    all_funders.to_csv(path_or_buf=response, index=False)
    return response
