import logging

import djclick as click
import pandas as pd
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery

from ukgrantmaking.models.grant import GOVERNMENT_EXCLUSIONS, Grant, GrantRecipient
from ukgrantmaking.utils import batched

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@click.command()
@click.argument("db_con", envvar="FTC_DB_URL")
@click.option("--company-batch-size", default=1_000)
def recipient_type(db_con, company_batch_size):
    with transaction.atomic():
        logging.info("Update recipient types")

        logging.info("Updating individuals")
        updated = GrantRecipient.objects.filter(
            type_registered=Grant.RecipientType.INDIVIDUAL,
            type_manual__isnull=True,
        ).update(
            type_manual=Grant.RecipientType.INDIVIDUAL,
        )
        logging.info(f"{updated} grants updated to individual")

        filters = [
            (
                Grant.RecipientType.CHARITY,
                (
                    Q(recipient_id__startswith="GB-CHC-")
                    | Q(recipient_id__startswith="GB-SC-")
                    | Q(recipient_id__startswith="GB-NIC-")
                ),
            ),
            (
                Grant.RecipientType.LOCAL_AUTHORITY,
                (
                    Q(recipient_id__startswith="GB-LAE-")
                    | Q(recipient_id__startswith="GB-LAS-")
                    | Q(recipient_id__startswith="GB-PLA-")
                    | Q(recipient_id__startswith="GB-LANI-")
                    | Q(recipient_id__startswith="GB-UKLA-")
                ),
            ),
            (
                Grant.RecipientType.COMMUNITY_INTEREST_COMPANY,
                Q(name__icontains="community interest company"),
            ),
            (
                Grant.RecipientType.COMMUNITY_INTEREST_COMPANY,
                Q(name__iendswith=" cic") & Q(recipient_id__startswith="GB-CIC-"),
            ),
            (
                Grant.RecipientType.LOCAL_AUTHORITY,
                (
                    Q(recipient_id__startswith="GB-UKPRN-")
                    | Q(recipient_id__startswith="GB-EDU-")
                )
                & Q(name__icontains="council"),
            ),
            (
                Grant.RecipientType.NHS,
                (
                    Q(recipient_id__startswith="GB-UKPRN-")
                    | Q(recipient_id__startswith="GB-EDU-")
                )
                & Q(name__icontains="nhs"),
            ),
            (
                Grant.RecipientType.UNIVERSITY,
                Q(name__icontains="university") & ~Q(name__icontains="third age"),
            ),
            (
                Grant.RecipientType.NHS,
                Q(recipient_id__startswith="GB-NHS-"),
            ),
            (
                Grant.RecipientType.EDUCATION,
                (
                    Q(recipient_id__startswith="GB-UKPRN-")
                    | Q(recipient_id__startswith="GB-EDU-")
                    | Q(recipient_id__startswith="GB-SCOTEDU-")
                    | Q(recipient_id__startswith="GB-WALEDU-")
                    | Q(recipient_id__startswith="GB-NIEDU-")
                ),
            ),
            (
                Grant.RecipientType.SPORTS_CLUB,
                Q(recipient_id__startswith="GB-CASC-"),
            ),
            (
                Grant.RecipientType.LOCAL_AUTHORITY,
                Q(name__iregex="(town|parish|community|county|district) Council"),
            ),
        ]
        for recipient_type, filter in filters:
            logging.info(f"Finding {recipient_type}")
            updated = GrantRecipient.objects.filter(
                Q(type_registered=Grant.RecipientType.ORGANISATION)
                & Q(type_manual__isnull=True)
                & filter
            ).update(
                type_manual=recipient_type,
            )
            logging.info(f"{updated:,.0f} grants updated to {recipient_type}")

        logging.info("Sort out company numbers")
        all_company_numbers = (
            GrantRecipient.objects.filter(
                recipient_id__startswith="GB-COH-",
                type_manual__isnull=True,
            )
            .values_list("recipient_id", flat=True)
            .distinct()
        )
        logging.info(f"{len(all_company_numbers)} company numbers to check")

        # process company numbers in batches
        for company_numbers in batched(all_company_numbers, company_batch_size):
            logging.info(f"Processing {len(company_numbers)} company numbers")

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
                    logging.warning(f"Unknown org type {org_type}")
                    continue

                updated = GrantRecipient.objects.filter(
                    recipient_id__in=charitable_companies.loc[
                        charitable_companies["organisationTypePrimary_id"] == org_type,
                        "company_id",
                    ].unique(),
                    type_manual__isnull=True,
                ).update(
                    type_manual=recipient_type,
                )
                logging.info(f"{updated} grants to charitable companies found")

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
                if org_type in (
                    "royal-charter-company",
                    "royal-charter",
                    "private-limited-guarant-nsc",
                    "private-limited-guarant-nsc-limited-exemption",
                    "company-limited-by-guarantee",
                ):
                    recipient_type = Grant.RecipientType.NON_PROFIT_COMPANY
                elif org_type in ("community-interest-company",):
                    recipient_type = Grant.RecipientType.COMMUNITY_INTEREST_COMPANY
                elif org_type in (
                    "charitable-incorporated-organisation",
                    "scottish-charitable-incorporated-organisation",
                ):
                    recipient_type = Grant.RecipientType.CHARITY
                elif org_type in (
                    "registered-society",
                    "registered-society-non-jurisdictional",
                    "industrial-and-provident-society",
                ):
                    recipient_type = Grant.RecipientType.MUTUAL
                elif org_type in (
                    "ltd",
                    "other",
                    "plc",
                    "llp",
                    "private-unlimited",
                    "limited-partnership",
                    "registered-overseas-entity",
                    "private-limited-shares-section-30-exemption",
                ):
                    recipient_type = Grant.RecipientType.PRIVATE_COMPANY
                else:
                    logging.warning(f"Unknown org type {org_type}")
                    continue

                updated = GrantRecipient.objects.filter(
                    recipient_id__in=all_companies.loc[
                        all_companies["CompanyCategory"] == org_type,
                        "company_id",
                    ].unique(),
                    type_manual__isnull=True,
                ).update(
                    type_manual=recipient_type,
                )
                logging.info(
                    f"{updated:,.0f} grants to nonprofit companies found as {recipient_type}",
                )

        progress = GrantRecipient.objects.values("type_manual").annotate(
            count=Count("recipient_id")
        )
        for p in progress:
            logging.info(f"{p['type_manual']}: {p['count']}")

        logging.info("Applying manual overrides from GrantRecipient to Grant")
        updated = (
            Grant.objects.select_related("recipient")
            .select_for_update()
            .filter(
                Q(recipient_type_manual__isnull=False)
                & Q(recipient__type_manual__in=Grant.RecipientType.values)
            )
            .update(
                recipient_type_manual=Subquery(
                    GrantRecipient.objects.filter(
                        recipient_id=OuterRef("recipient_id")
                    ).values("type_manual")[:1]
                ),
            )
        )
        logging.info(f"{updated} grants updated with recipient type manual")

        logging.info("Update government exclusion list")
        for inclusion, filter in GOVERNMENT_EXCLUSIONS:
            updated = Grant.objects.filter(
                inclusion=Grant.InclusionStatus.UNSURE,
                funding_organisation_type__in=[
                    Grant.FunderType.CENTRAL_GOVERNMENT,
                    Grant.FunderType.LOCAL_GOVERNMENT,
                    Grant.FunderType.DEVOLVED_GOVERNMENT,
                ],
                recipient_type_manual__in=filter,
            ).update(
                inclusion=inclusion,
            )
            logging.info(f"{updated} grants updated to {inclusion}")

        progress = (
            Grant.objects.filter(
                funding_organisation_type__in=[
                    Grant.FunderType.CENTRAL_GOVERNMENT,
                    Grant.FunderType.LOCAL_GOVERNMENT,
                    Grant.FunderType.DEVOLVED_GOVERNMENT,
                ]
            )
            .values("inclusion")
            .annotate(count=Count("grant_id"))
        )
        for p in progress:
            logging.info(f"{p['inclusion']}: {p['count']}")
