from itertools import batched

import djclick as click
import pandas as pd
from django.db import transaction
from django.db.models import Count, Q

from ukgrantmaking.models import Grant


@click.command()
@click.argument("db_con", envvar="FTC_DB_URL")
@click.option("--company-batch-size", default=1_000)
def recipient_type(db_con, company_batch_size):
    with transaction.atomic():
        click.secho("Update recipient types", fg="green")

        click.secho("Updating individuals", fg="green")
        updated = Grant.objects.filter(
            recipient_type=Grant.RecipientType.INDIVIDUAL,
            recipient_type_manual__isnull=True,
        ).update(
            recipient_type_manual=Grant.RecipientType.INDIVIDUAL,
        )
        click.secho(f"{updated} grants updated to individual", fg="green")

        filters = [
            (
                Grant.RecipientType.CHARITY,
                Q(
                    Q(recipient_organisation_id__startswith="GB-CHC-")
                    | Q(recipient_organisation_id__startswith="GB-SC-")
                    | Q(recipient_organisation_id__startswith="GB-NIC-")
                ),
            ),
            (
                Grant.RecipientType.LOCAL_AUTHORITY,
                Q(
                    Q(recipient_organisation_id__startswith="GB-LAE-")
                    | Q(recipient_organisation_id__startswith="GB-LAS-")
                    | Q(recipient_organisation_id__startswith="GB-PLA-")
                    | Q(recipient_organisation_id__startswith="GB-LANI-")
                    | Q(recipient_organisation_id__startswith="GB-UKLA-")
                ),
            ),
            (
                Grant.RecipientType.COMMUNITY_INTEREST_COMPANY,
                Q(recipient_organisation_name__icontains="community interest company"),
            ),
            (
                Grant.RecipientType.COMMUNITY_INTEREST_COMPANY,
                Q(
                    Q(recipient_organisation_name__iendswith=" cic")
                    & Q(recipient_organisation_id__startswith="GB-CIC-")
                ),
            ),
            (
                Grant.RecipientType.LOCAL_AUTHORITY,
                Q(
                    Q(
                        Q(
                            Q(recipient_organisation_id__startswith="GB-UKPRN-")
                            | Q(recipient_organisation_id__startswith="GB-EDU-")
                        )
                    )
                    & Q(recipient_organisation_name__icontains="council")
                ),
            ),
            (
                Grant.RecipientType.NHS,
                Q(
                    Q(
                        Q(
                            Q(recipient_organisation_id__startswith="GB-UKPRN-")
                            | Q(recipient_organisation_id__startswith="GB-EDU-")
                        )
                    )
                    & Q(recipient_organisation_name__icontains="nhs")
                ),
            ),
            (
                Grant.RecipientType.UNIVERSITY,
                Q(
                    Q(recipient_organisation_name__icontains="university")
                    & ~Q(recipient_organisation_name__icontains="third age")
                ),
            ),
            (
                Grant.RecipientType.NHS,
                Q(recipient_organisation_id__startswith="GB-NHS-"),
            ),
            (
                Grant.RecipientType.EDUCATION,
                Q(
                    Q(
                        Q(
                            Q(recipient_organisation_id__startswith="GB-UKPRN-")
                            | Q(recipient_organisation_id__startswith="GB-EDU-")
                            | Q(recipient_organisation_id__startswith="GB-SCOTEDU-")
                            | Q(recipient_organisation_id__startswith="GB-WALEDU-")
                            | Q(recipient_organisation_id__startswith="GB-NIEDU-")
                        )
                    )
                ),
            ),
            (
                Grant.RecipientType.SPORTS_CLUB,
                Q(
                    Q(recipient_organisation_id__startswith="GB-CASC-")
                    | Q(funding_organisation_name="Sport England")
                ),
            ),
            (
                Grant.RecipientType.LOCAL_AUTHORITY,
                Q(
                    recipient_organisation_name__iregex="(town|parish|community|county|district) Council"
                ),
            ),
        ]
        for recipient_type, filter in filters:
            click.secho(f"Finding {recipient_type}", fg="green")
            updated = Grant.objects.filter(
                Q(recipient_type=Grant.RecipientType.ORGANISATION)
                & Q(recipient_type_manual__isnull=True)
                & filter
            ).update(
                recipient_type_manual=recipient_type,
            )
            click.secho(f"{updated} grants updated to {recipient_type}", fg="green")

        click.secho("Sort out company numbers", fg="green")
        all_company_numbers = (
            Grant.objects.filter(
                recipient_organisation_id__startswith="GB-COH-",
                recipient_type_manual__isnull=True,
            )
            .values_list("recipient_organisation_id", flat=True)
            .distinct()
        )
        click.secho(f"{len(all_company_numbers)} company numbers to check", fg="green")

        # process company numbers in batches
        for company_numbers in batched(all_company_numbers, company_batch_size):
            click.secho(
                f"Processing {len(company_numbers)} company numbers", fg="green"
            )

            charitable_companies = pd.read_sql(
                """
                SELECT org_id,
                    "organisationTypePrimary_id",
                    'GB-COH-' || "companyNumber" as company_id
                FROM ftc_organisation
                WHERE "companyNumber" IN %(org_ids)s
                    AND org_id NOT LIKE 'GB-COH-%%'
                """,
                con=db_con,
                params={
                    "org_ids": tuple(
                        c.replace("GB-COH-", "")
                        for c in company_numbers
                        if isinstance(c, str)
                    )
                },
            )
            for org_type in charitable_companies["organisationTypePrimary_id"].unique():
                recipient_type = None
                if org_type == "registered-charity":
                    recipient_type = Grant.RecipientType.CHARITY
                else:
                    click.secho(f"Unknown org type {org_type}", fg="red")
                    continue

                updated = Grant.objects.filter(
                    recipient_organisation_id__in=charitable_companies.loc[
                        charitable_companies["organisationTypePrimary_id"] == org_type,
                        "company_id",
                    ].unique(),
                    recipient_type_manual__isnull=True,
                ).update(
                    recipient_type_manual=recipient_type,
                )
                click.secho(
                    f"{updated} grants to charitable companies found", fg="green"
                )

            all_companies = pd.read_sql(
                """
                SELECT "CompanyCategory",
                    'GB-COH-' || "CompanyNumber" as company_id
                FROM companies_company
                WHERE "CompanyNumber" IN %(org_ids)s
                """,
                con=db_con,
                params={
                    "org_ids": tuple(
                        c.replace("GB-COH-", "")
                        for c in company_numbers
                        if isinstance(c, str)
                    )
                },
            )
            for org_type in all_companies["CompanyCategory"].unique():
                recipient_type = None
                if org_type == "company-limited-by-guarantee":
                    recipient_type = Grant.RecipientType.NON_PROFIT_COMPANY
                elif org_type == "community-interest-company":
                    recipient_type = Grant.RecipientType.COMMUNITY_INTEREST_COMPANY
                elif org_type == "scottish-charitable-incorporated-organisation":
                    recipient_type = Grant.RecipientType.CHARITY
                elif org_type == "registered-society":
                    recipient_type = Grant.RecipientType.MUTUAL
                elif org_type == "charitable-incorporated-organisation":
                    recipient_type = Grant.RecipientType.CHARITY
                elif org_type == "royal-charter-company":
                    recipient_type = Grant.RecipientType.NON_PROFIT_COMPANY
                elif org_type in (
                    "ltd",
                    "other",
                    "plc",
                    "llp",
                    "private-unlimited",
                    "limited-partnership",
                    "registered-overseas-entity",
                ):
                    recipient_type = Grant.RecipientType.PRIVATE_COMPANY
                else:
                    click.secho(f"Unknown org type {org_type}", fg="red")
                    continue

                updated = Grant.objects.filter(
                    recipient_organisation_id__in=all_companies.loc[
                        all_companies["CompanyCategory"] == org_type,
                        "company_id",
                    ].unique(),
                    recipient_type_manual__isnull=True,
                ).update(
                    recipient_type_manual=recipient_type,
                )
                click.secho(
                    f"{updated} grants to nonprofit companies found as {recipient_type}",
                    fg="green",
                )

        progress = Grant.objects.values("recipient_type_manual").annotate(
            count=Count("grant_id")
        )
        for p in progress:
            click.secho(f"{p['recipient_type_manual']}: {p['count']}", fg="green")

        click.secho("Update government exclusion list", fg="green")
        exclusions = [
            (
                Grant.InclusionStatus.LOCAL_AUTHORITY_GRANT,
                Q(recipient_type_manual=Grant.RecipientType.LOCAL_AUTHORITY),
            ),
            (
                Grant.InclusionStatus.GRANT_TO_EDUCATION,
                Q(recipient_type_manual=Grant.RecipientType.EDUCATION),
            ),
            (
                Grant.InclusionStatus.PRIVATE_SECTOR_GRANT,
                Q(recipient_type_manual=Grant.RecipientType.PRIVATE_COMPANY),
            ),
        ]
        for inclusion, filter in exclusions:
            updated = Grant.objects.filter(
                Q(inclusion=Grant.InclusionStatus.UNSURE)
                & Q(funding_organisation_type=Grant.FunderType.CENTRAL_GOVERNMENT)
                & filter
            ).update(
                inclusion=inclusion,
            )
            click.secho(f"{updated} grants updated to {inclusion}", fg="green")

        progress = (
            Grant.objects.filter(
                funding_organisation_type=Grant.FunderType.CENTRAL_GOVERNMENT
            )
            .values("inclusion")
            .annotate(count=Count("grant_id"))
        )
        for p in progress:
            click.secho(f"{p['inclusion']}: {p['count']}", fg="green")
