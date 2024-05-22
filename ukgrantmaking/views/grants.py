from io import BytesIO

import pandas as pd
from caradoc import DataOutput, FinancialYear
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import slugify

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
    grant_crosstab,
    grant_summary,
    grant_table,
    grants_by_country,
    grants_by_region,
    grants_by_what,
    grants_by_who,
    number_of_grants_by_recipient,
    recipient_size_by_amount_awarded,
    recipient_types,
    recipients_by_size,
    who_funds_with_who,
)


@login_required
def all_grants_csv(request, fy):
    current_fy = FinancialYear(fy)
    all_grants = get_all_grants(current_fy)

    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="all-grants-{current_fy}.csv"'
        },
    )
    all_grants.to_csv(path_or_buf=response, index=False)
    return response


def for_flourish(grants):
    categories = {
        "Charity": ("Charity", "Total"),
        "Grantmaker": ("Grantmaker", "Total"),
        "Lottery Distributor": ("Lottery", "Lottery Distributor"),
        "Government": ("Government", "Total"),
        "Other": ("Other", "Donor Advised Fund"),
    }
    simple_segments = {
        "Government": ("Government", "Total"),
        "Community Foundation": ("Grantmaker", "Community Foundation"),
        "Corporate Foundation": ("Grantmaker", "Corporate Foundation"),
        "Family Foundation": ("Grantmaker", "Family Foundation"),
        "Fundraising Grantmaker": ("Grantmaker", "Fundraising Grantmaker"),
        "General grantmaker": ("Grantmaker", "General grantmaker"),
        "Government/Lottery Endowed": ("Grantmaker", "Government/Lottery Endowed"),
        "Member/Trade Funded": ("Grantmaker", "Member/Trade Funded"),
        "Lottery Distributors": ("Lottery", "Lottery Distributor"),
        "Charity": ("Charity", "Total"),
        "All grantmakers": ("Total", "Total"),
    }

    charts = [
        # name, function, categories, flip, drop unknown
        ("Recipient type", recipient_types, categories, False, None, True),
        (
            "Size of grant recipients",
            recipients_by_size,
            simple_segments,
            True,
            "Unknown",
            True,
        ),
        (
            "Recipients by country",
            grants_by_country,
            simple_segments,
            False,
            "Unknown",
            False,
        ),
        (
            "Communities served",
            grants_by_who,
            simple_segments,
            False,
            None,
            False,
        ),
        (
            "Themes",
            grants_by_what,
            simple_segments,
            False,
            None,
            False,
        ),
        (
            "Grant duration",
            grant_by_duration,
            simple_segments,
            True,
            None,
            False,
        ),
        (
            "Grant size",
            grant_by_size,
            simple_segments,
            True,
            "Unknown",
            False,
        ),
        (
            "Recipient size by grant awarded",
            recipient_size_by_amount_awarded,
            None,
            True,
            "Unknown",
            False,
        ),
    ]
    for (
        chart_name,
        chart_function,
        chart_categories,
        chart_flip,
        drop_label,
        use_total,
    ) in charts:
        chart_dfs = {
            "Number of grants": chart_function(grants),
            "Grant amount": chart_function(
                grants,
                values_field="amount_awarded_GBP",
            ),
        }
        output_dfs = {}
        output_dfs_pc = {}
        for label, df in chart_dfs.items():
            if chart_categories:
                output_dfs[label] = pd.DataFrame(
                    {k: df.loc[v, :] for k, v in chart_categories.items()}
                )
            else:
                output_dfs[label] = df
            if drop_label:
                output_dfs[label] = output_dfs[label].drop(
                    drop_label, axis=0, errors="ignore"
                )
            if use_total:
                output_dfs_pc[label] = output_dfs[label].divide(
                    output_dfs[label].loc["Total", :], axis=1
                )
            else:
                output_dfs_pc[label] = output_dfs[label].divide(
                    output_dfs[label].drop("Total", axis=0).sum(axis=0), axis=1
                )
            output_dfs_pc[label] = (
                output_dfs_pc[label].multiply(100).round(2).drop("Total", axis=0)
            )
            if chart_flip:
                output_dfs[label] = output_dfs[label].T
                output_dfs_pc[label] = output_dfs_pc[label].T

        yield (
            f"{chart_name} (percentage)",
            pd.concat(output_dfs_pc).rename_axis(
                ["Metric", "Segment" if chart_flip else chart_name]
            ),
        )
        # yield (
        #     chart_name,
        #     pd.concat(output_dfs).rename_axis(["Metric", "Segment"]),
        # )

    yield ("Recipients by number of grants", number_of_grants_by_recipient(grants))

    summary = (
        grant_summary(grants)
        .drop(
            [("Total", "Total"), ("Unknown", "Unknown"), ("Flurgle", "Flurgle")],
            errors="ignore",
            axis=0,
        )
        .reset_index()
    )
    yield (
        "Median grant size",
        pd.crosstab(
            summary["segment"],
            summary["category"],
            values=summary["Median amount"],
            aggfunc="sum",
        )
        .fillna(pd.NA)
        .drop("Total", axis=0),
    )

    by_size = grant_by_size(grants)
    by_size = by_size.divide(by_size["Total"], axis=0).multiply(100).round(2)
    by_size = (
        by_size[["£100k to £1m", "Over £1m"]]
        .sum(axis=1)
        .drop(
            [("Total", "Total"), ("Unknown", "Unknown"), ("Flurgle", "Flurgle")],
            errors="ignore",
            axis=0,
        )
        .rename("Over £100k")
        .reset_index()
    )
    yield (
        "Proportion of grants over £100k",
        pd.crosstab(
            by_size["segment"],
            by_size["category"],
            values=by_size["Over £100k"],
            aggfunc="sum",
        )
        .fillna(pd.NA)
        .drop("Total", axis=0),
    )


@login_required
def financial_year_grants_simple(request, fy, filetype="html"):
    current_fy = FinancialYear(fy)
    output = DataOutput()

    all_grants = get_all_grants(current_fy)

    criteria = all_grants["recipient_type"] != "Individual"

    for chart_name, chart_output in for_flourish(all_grants[criteria]):
        output.add_table(chart_output, chart_name)

    if filetype == "xlsx":
        buffer = BytesIO()
        output.write(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            f"attachment; filename=grants-simple-{fy}.xlsx"
        )
        return response

    return render(
        request,
        "financial_year.html.j2",
        {
            "fy": fy,
            "output": output,
            "skip_sheets": ["All general grantmakers"],
            "links": {
                "Download as XLSX": reverse(
                    "financial_year_grants_simple_xlsx", kwargs={"fy": fy}
                ),
                "Download all grants as CSV": reverse(
                    "all_grants_csv", kwargs={"fy": fy}
                ),
                "Back to full tables": reverse(
                    "financial_year_grants", kwargs={"fy": fy}
                ),
            },
        },
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
        "Community Foundations": {
            "criteria": (all_grants["segment"].isin(["Community Foundation"])),
        },
        "London": {
            "criteria": (all_grants["london_category"].notnull()),
        },
    }

    criteria = summaries["Grants to organisations"]["criteria"]
    for chart_name, chart_output in for_flourish(all_grants[criteria]):
        output.add_table(chart_output, "For flourish", title=chart_name)

    for summary_name, summary_filters in summaries.items():
        summary_title = summary_name
        if filetype == "xlsx":
            summary_title = slugify(summary_name)[0:31]

        if summary_name == "London":
            output.add_table(
                grant_summary(
                    all_grants[summary_filters["criteria"]],
                    groupby=["london_category"],
                ),
                summary_title,
                title="London scale",
            )
            output.add_table(
                grant_crosstab(
                    all_grants[summary_filters["criteria"]],
                    column_field="london_category",
                ),
                summary_title,
                title="London scale by segment",
            )
            output.add_table(
                grant_by_size(
                    all_grants[summary_filters["criteria"]], groupby=["london_category"]
                ),
                summary_title,
                title="Summary by grant size",
            )
            output.add_table(
                grant_by_size(
                    all_grants[summary_filters["criteria"]],
                    groupby=["london_category"],
                    values_field="amount_awarded_GBP",
                ),
                summary_title,
                title="Summary by grant size (by amount awarded)",
            )
            output.add_table(
                grant_by_duration(
                    all_grants[summary_filters["criteria"]], groupby=["london_category"]
                ),
                summary_title,
                title="Summary by duration",
            )
            output.add_table(
                grant_by_duration(
                    all_grants[summary_filters["criteria"]],
                    groupby=["london_category"],
                    values_field="amount_awarded_GBP",
                ),
                summary_title,
                title="Summary by duration (by amount awarded)",
            )
            continue

        output.add_table(
            grant_summary(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="Summary",
        )
        output.add_table(
            grant_by_size(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="Summary by grant size",
        )
        output.add_table(
            grant_by_size(
                all_grants[summary_filters["criteria"]],
                values_field="amount_awarded_GBP",
            ),
            summary_title,
            title="Summary by grant size (by amount awarded)",
        )
        output.add_table(
            grant_by_duration(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="Summary by duration",
        )
        output.add_table(
            grant_by_duration(
                all_grants[summary_filters["criteria"]],
                values_field="amount_awarded_GBP",
            ),
            summary_title,
            title="Summary by duration (by amount awarded)",
        )

        # recipients by country/region
        output.add_table(
            grants_by_region(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="By Region (by number of grants)",
        )
        output.add_table(
            grants_by_region(
                all_grants[summary_filters["criteria"]],
                values_field="amount_awarded_GBP",
            ),
            summary_title,
            title="By Region (by amount awarded)",
        )
        output.add_table(
            grants_by_country(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="By Country (by number of grants)",
        )
        output.add_table(
            grants_by_country(
                all_grants[summary_filters["criteria"]],
                values_field="amount_awarded_GBP",
            ),
            summary_title,
            title="By Country (by amount awarded)",
        )

        # recipients by number of grants
        output.add_table(
            number_of_grants_by_recipient(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="Recipients by number of grants",
        )

        if summary_name in (
            "Grants to individuals",
            "Community Foundations",
            "London",
        ):
            output.add_table(
                grant_summary(
                    all_grants[summary_filters["criteria"]],
                    groupby=["funder_id", "funder_name", "segment"],
                ).sort_values("Grant amount (£m)", ascending=False),
                summary_title,
                title="By funder",
            )

        if summary_name == "Grants to individuals":
            for field in [
                "recipient_individual_primary_grant_reason",
                "recipient_individual_secondary_grant_reason",
                "recipient_individual_grant_purpose",
            ]:
                output.add_table(
                    grant_summary(
                        all_grants[summary_filters["criteria"]].explode(
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
                    summary_title,
                    title=(
                        field.replace("recipient_individual_", "")
                        .replace("_", " ")
                        .title()
                    ),
                )
        else:
            output.add_table(
                recipient_types(all_grants[summary_filters["criteria"]]),
                summary_title,
                title="Recipient type",
            )
            output.add_table(
                recipient_types(
                    all_grants[summary_filters["criteria"]],
                    values_field="amount_awarded_GBP",
                ),
                summary_title,
                title="Recipient type (by amount awarded)",
            )
            output.add_table(
                recipients_by_size(all_grants[summary_filters["criteria"]]),
                summary_title,
                title="Recipients by size",
            )
            output.add_table(
                recipients_by_size(
                    all_grants[summary_filters["criteria"]],
                    values_field="amount_awarded_GBP",
                ),
                summary_title,
                title="Recipients by size (by amount awarded)",
            )

            output.add_table(
                grant_summary(
                    all_grants[summary_filters["criteria"]],
                    groupby=["recipient_type"],
                ),
                summary_title,
                title="Recipients summary",
            )

            for field in [
                "recipient__who",
                "recipient__what",
                "recipient__how",
            ]:
                output.add_table(
                    grant_summary(
                        all_grants[
                            summary_filters["criteria"] & all_grants[field].notnull()
                        ].explode(field),
                        groupby=[field],
                    )
                    .reset_index()
                    .rename(
                        columns={
                            field: "Category",
                        }
                    ),
                    summary_title,
                    title="CC Classification: "
                    + field.replace("recipient__", "").title(),
                )
            # output.add_table(
            #     recipients_by_scale(all_grants[summary_filters["criteria"]]),
            #     "Recipients by scale",
            #     title=summary_title,
            # )

        # who funds with who
        wfww = who_funds_with_who(all_grants[summary_filters["criteria"]])
        if len(wfww) > 0:
            output.add_table(
                who_funds_with_who(all_grants[summary_filters["criteria"]]),
                summary_title if filetype == "html" else f"wfww-{summary_title}"[0:31],
                title="Who funds with who",
            )

    funders = list(
        Funder.objects.filter(included=True)
        .exclude(segment=FunderSegment.CHARITY)
        .values_list("org_id", flat=True)
    )
    funders.extend(
        [
            "GB-CHC-1203784",
            "GB-CHC-1122052",
            "GB-COH-00357963",
            "GB-CHC-1122052",
            "GB-CHC-1203576",
            "GB-CHC-1187441",
            "GB-CHC-1194447",
            "GB-CHC-205629",
        ]
    )
    output.add_table(
        grant_table(
            all_grants[all_grants["recipient_id"].isin(funders)],
            columns=DEFAULT_COLUMNS
            + ["segment", "recipient_id"]
            + (["description"] if filetype == "xlsx" else []),
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
            "links": {
                "Download as XLSX": reverse(
                    "financial_year_grants_xlsx", kwargs={"fy": fy}
                ),
                "Download all grants as CSV": reverse(
                    "all_grants_csv", kwargs={"fy": fy}
                ),
                "Simple tables": reverse("financial_year_grants", kwargs={"fy": fy}),
            },
        },
    )
