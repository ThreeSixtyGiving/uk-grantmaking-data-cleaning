from io import BytesIO

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
    grant_summary,
    grant_table,
    grants_by_country,
    grants_by_region,
    number_of_grants_by_recipient,
    recipient_types,
    recipients_by_size,
    who_funds_with_who,
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
            "criteria": (
                all_grants["recipient__london_aoo"].eq(True)
                | all_grants["beneficiary_location_rgn"].eq("E12000007")
            ),
        },
    }

    for summary_title, summary_filters in summaries.items():
        if filetype == "xlsx":
            summary_title = slugify(summary_title)[0:31]
        output.add_table(
            grant_summary(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="Summary",
        )
        output.add_table(
            grant_by_size(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="Summary by size",
        )
        output.add_table(
            grant_by_size(
                all_grants[summary_filters["criteria"]],
                values_field="amount_awarded_GBP",
            ),
            summary_title,
            title="Summary by size (by amount awarded)",
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

        for field in [
            "recipient__who",
            "recipient__what",
            "recipient__how",
        ]:
            output.add_table(
                grant_summary(
                    all_grants[summary_filters["criteria"]].explode(field),
                    groupby=[field],
                )
                .reset_index()
                .rename(
                    columns={
                        field: "Category",
                    }
                ),
                summary_title,
                title="CC Classification: " + field.replace("recipient__", "").title(),
            )

        # recipients by number of grants
        output.add_table(
            number_of_grants_by_recipient(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="Recipients by number of grants",
        )

        # who funds with who
        output.add_table(
            who_funds_with_who(all_grants[summary_filters["criteria"]]),
            summary_title,
            title="Who funds with who",
        )

        if summary_title in (
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

        if summary_title == "Grants to individuals":
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
            # output.add_table(
            #     recipients_by_scale(all_grants[summary_filters["criteria"]]),
            #     "Recipients by scale",
            #     title=summary_title,
            # )

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
        output.add_table(
            grant_table(
                all_grants,
                columns=[c for c in all_grants.columns if c not in ["grant_id"]],
                n=None,
            ),
            "All grants",
        )

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
